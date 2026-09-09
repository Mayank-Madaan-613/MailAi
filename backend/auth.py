3import base64
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,RedirectResponse 
from google_auth_oauthlib.flow import Flow
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from googleapiclient.discovery import build
from bs4 import BeautifulSoup
from apicall import Prompt

app=FastAPI()
origins=["http://localhost:5500","http://127.0.0.1:5500"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins)
app.add_middleware(SessionMiddleware, 
    secret_key="your-very-secure-random-secret-key", 
    session_cookie="fapi_session",                   
    max_age=3600,                                    
    same_site="lax",                                 
    https_only=False                                 
)
def extract_detail(mail:dict):
    payload=mail["payload"]
    headers=payload.get("headers")
    date=sub=From=To=None
    for item in headers:
        if item.get("name")=="Date":
            date=item.get("value")
        elif item.get("name")=="From":
            From=item.get("value")
        elif item.get("name")=="To":
            To=item.get("value")
        elif item.get("name")=="Subject":
            sub=item.get("value")
    return {"Date":date,"From":From,"To":To,"subject":sub}
def get_email_body(payload):
    if payload.get("body",{}).get("data"):
        data=payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode()
    for part in payload.get("parts",[]):
        if part.get("mimeType")=="text/plain":
            body=get_email_body(part)
            return body
        body=get_email_body(part)
        soup=BeautifulSoup(body,"html.parser")
        txt=soup.get_text(separator="\n",strip=True)
        return txt 


SCOPES=["openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile","https://www.googleapis.com/auth/gmail.readonly"]

Redirect_uri="http://localhost:8000/auth/callback"
@app.get('/',response_class=HTMLResponse)
async def open():
    return '''<h1>Mail Ai</h1>
    <a href="/login">
    <button>LogIn with Google</button></a>'''



@app.get('/login')
async def login(request:Request):
    flow=Flow.from_client_secrets_file("client_secret.json",scopes=SCOPES)
    flow.redirect_uri=Redirect_uri
    print("FLOW Created")  
    authorization_url,state=flow.authorization_url(access_type="offline",include_granted_scopes="true",prompt="consent")
    request.session["code_verifier"]=flow.code_verifier
    request.session['state']=state
    print(authorization_url)
    return RedirectResponse(authorization_url)


@app.get('/auth/callback',response_class=HTMLResponse)
async def callback(request:Request):
    return_state=request.session.get('state')
    saved_state=request.query_params.get("state")
    if return_state!=saved_state:
        return{'message':"INVALID OAUTH REQUEST"}
    code=request.query_params.get("code")
    flow=Flow.from_client_secrets_file("client_secret.json",scopes=SCOPES)
    flow.redirect_uri=Redirect_uri
    flow.code_verifier=request.session["code_verifier"]
    flow.fetch_token(code=request.query_params.get('code'))
    credentials=flow.credentials
    service=build("gmail",'v1',credentials=credentials)
    messages=service.users().messages().list(q="in:inbox category:primary",userId="me",maxResults=5).execute()
    result=messages.get("messages",[])
    message_id=result[0]['id']
    email=service.users().messages().get(userId="me",id=message_id,format="full").execute()
    payload=email["payload"]
    body=get_email_body(payload)
    details=extract_detail(email)
    details["Body"]=body
    obj=Prompt()
    outp=obj.generate(details)
    return f'''<div>f{outp}</div>'''

