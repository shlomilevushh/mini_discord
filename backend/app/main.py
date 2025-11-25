from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form, Cookie, Response, HTTPException, status, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import re
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from .database import (
    init_database, create_user, verify_user, get_user_by_id, get_user_by_username,
    send_friend_request, get_pending_friend_requests, 
    accept_friend_request, decline_friend_request, get_friends, get_friends_with_status,
    update_user_status, save_message, get_chat_history,
    create_server, get_user_servers, get_server_by_id, send_server_invite,
    get_pending_server_invites, accept_server_invite, decline_server_invite,
    create_channel, get_server_channels, join_channel, leave_channel,
    get_channel_members, save_channel_message, get_channel_messages
)

app = FastAPI()

# Secret key for session management (in production, use environment variable)
SECRET_KEY = "your-secret-key-change-this-in-production"
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the directory of the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up two levels to reach the project root, then into frontend/templates
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "frontend", "templates")
STATIC_DIR = os.path.join(PROJECT_ROOT, "frontend", "static")
PAGES_DIR = os.path.join(PROJECT_ROOT, "frontend", "pages")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Mount static files (for avatars) and pages (for CSS/JS)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/pages", StaticFiles(directory=PAGES_DIR), name="pages")

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """Validate password requirements"""
    if len(password) < 8 or len(password) > 16:
        return False, "Password must be 8-16 characters long"
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least 1 letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least 1 number"
    return True, ""

def create_session(user_id: int) -> str:
    """Create a session token"""
    return serializer.dumps({"user_id": user_id})

def verify_session(session_token: str) -> Optional[int]:
    """Verify session token and return user_id, None if invalid/expired"""
    if not session_token:
        return None
    try:
        data = serializer.loads(session_token, max_age=86400)  # 24 hours
        return data.get("user_id")
    except (BadSignature, SignatureExpired):
        return None
    except Exception as e:
        print(f"Session verification error: {e}")
        return None

async def get_current_user_optional(session: str = Cookie(None)) -> Optional[dict]:
    """
    Dependency to get current user from session (returns None if not logged in)
    Use this for pages that work with or without login
    """
    if not session:
        return None
    user_id = verify_session(session)
    if not user_id:
        return None
    return get_user_by_id(user_id)

async def get_current_user_required(session: str = Cookie(None)) -> dict:
    """
    Dependency to get current user from session (raises exception if not logged in)
    Use this for protected pages that require authentication
    """
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - no session cookie"
        )
    
    user_id = verify_session(session)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@app.get("/", response_class=HTMLResponse)
async def login(request: Request, user: Optional[dict] = Depends(get_current_user_optional)):
    # Check if already logged in
    return templates.TemplateResponse("login.html", {
        "request": request,
        "already_logged_in": user is not None,
        "username": user["username"] if user else None
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, user: Optional[dict] = Depends(get_current_user_optional)):
    # Check if already logged in
    return templates.TemplateResponse("register.html", {
        "request": request,
        "already_logged_in": user is not None,
        "username": user["username"] if user else None
    })

@app.post("/register")
async def register_post(
    email: str = Form(...), 
    username: str = Form(...), 
    password: str = Form(...),
    avatar: str = Form(...)
):
    """
    Handle registration POST request with validation
    """
    # Validate email
    if not validate_email(email):
        return JSONResponse({
            "success": False,
            "message": "Invalid email format!"
        })
    
    # Validate password
    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return JSONResponse({
            "success": False,
            "message": error_msg
        })
    
    # Validate avatar selection
    valid_avatars = ["avatar1", "avatar2", "avatar3", "avatar4", "avatar5", "avatar6"]
    if avatar not in valid_avatars:
        return JSONResponse({
            "success": False,
            "message": "Invalid avatar selection!"
        })
    
    # Create user in database
    result = create_user(email, username, password, avatar)
    return JSONResponse(result)

@app.post("/login")
async def login_post(email: str = Form(...), password: str = Form(...)):
    """
    Handle login POST request with email and password
    """
    result = verify_user(email, password)
    
    # Create JSON response
    json_response = JSONResponse(result)
    
    if result["success"]:
        # Set user status to online
        user_id = result["user"]["id"]
        update_user_status(user_id, 'online')
        
        # Create session cookie and add to response
        session_token = create_session(user_id)
        json_response.set_cookie(
            key="session",
            value=session_token,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite="lax"
        )
    
    return json_response

@app.get("/logout")
async def logout(user: dict = Depends(get_current_user_optional)):
    """Logout and clear session"""
    # Set user status to offline if they're logged in
    if user:
        update_user_status(user['id'], 'offline')
    
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session")
    return response

@app.get("/home", response_class=HTMLResponse)
async def home(request: Request, user: dict = Depends(get_current_user_required), session: str = Cookie(None)):
    """
    Protected route - Home page with friend list and servers
    Automatically handles authorization via dependency injection
    """
    # Get user's friends with status and friend requests
    friends = get_friends_with_status(user['id'])
    friend_requests = get_pending_friend_requests(user['id'])
    
    # Get user's servers and server invites
    servers = get_user_servers(user['id'])
    server_invites = get_pending_server_invites(user['id'])
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user,
        "session_token": session,
        "friends": friends,
        "friend_requests": friend_requests,
        "servers": servers,
        "server_invites": server_invites
    })

# Friend system API endpoints
@app.post("/api/friends/request")
async def send_friend_request_endpoint(
    username: str = Form(...),
    user: dict = Depends(get_current_user_required)
):
    """Send a friend request to another user"""
    result = send_friend_request(user['id'], username)
    return JSONResponse(result)

@app.post("/api/friends/accept/{request_id}")
async def accept_friend_request_endpoint(
    request_id: int,
    user: dict = Depends(get_current_user_required)
):
    """Accept a friend request"""
    result = accept_friend_request(request_id, user['id'])
    return JSONResponse(result)

@app.post("/api/friends/decline/{request_id}")
async def decline_friend_request_endpoint(
    request_id: int,
    user: dict = Depends(get_current_user_required)
):
    """Decline a friend request"""
    result = decline_friend_request(request_id, user['id'])
    return JSONResponse(result)

@app.get("/api/friends")
async def get_friends_endpoint(user: dict = Depends(get_current_user_required)):
    """Get list of friends"""
    friends = get_friends(user['id'])
    return JSONResponse({"success": True, "friends": friends})

@app.get("/api/friends/requests")
async def get_friend_requests_endpoint(user: dict = Depends(get_current_user_required)):
    """Get pending friend requests"""
    requests = get_pending_friend_requests(user['id'])
    return JSONResponse({"success": True, "requests": requests})

# Status management endpoints
@app.post("/api/status")
async def update_status_endpoint(
    status: str = Form(...),
    user: dict = Depends(get_current_user_required)
):
    """Update user status (online, offline, invisible)"""
    result = update_user_status(user['id'], status)
    return JSONResponse(result)

@app.get("/api/friends/status")
async def get_friends_status_endpoint(user: dict = Depends(get_current_user_required)):
    """Get friends list with their online status"""
    friends = get_friends_with_status(user['id'])
    return JSONResponse({"success": True, "friends": friends})

# Messaging endpoints
@app.post("/api/messages/send")
async def send_message_endpoint(
    receiver_id: int = Form(...),
    message: str = Form(...),
    user: dict = Depends(get_current_user_required)
):
    """Send a private message to a friend"""
    result = save_message(user['id'], receiver_id, message)
    return JSONResponse(result)

@app.get("/api/messages/{friend_id}")
async def get_messages_endpoint(
    friend_id: int,
    user: dict = Depends(get_current_user_required)
):
    """Get chat history with a specific friend"""
    messages = get_chat_history(user['id'], friend_id)
    return JSONResponse({"success": True, "messages": messages})

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom exception handler for authentication failures
    Redirects to login page instead of showing error
    """
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        # For API requests, return JSON
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )
                # For page requests, redirect to login
        return RedirectResponse(url="/?error=unauthorized", status_code=302)
    
    # Handle 404 and other errors
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )    # For other HTTP exceptions, return JSON
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# ============================================
# SERVER ROUTES
# ============================================

@app.post("/create-server")
async def create_server_route(
    name: str = Form(...),
    current_user: dict = Depends(get_current_user_required)
):
    """Create a new server"""
    result = create_server(name, current_user['id'])
    return JSONResponse(content=result)


@app.get("/my-servers")
async def get_my_servers_route(current_user: dict = Depends(get_current_user_required)):
    """Get all servers the user is a member of"""
    servers = get_user_servers(current_user['id'])
    return JSONResponse(content={"servers": servers})


@app.get("/server/{server_id}")
async def get_server_route(
    server_id: int,
    current_user: dict = Depends(get_current_user_required)
):
    """Get server details"""
    server = get_server_by_id(server_id)
    if not server:
        return JSONResponse(
            content={"success": False, "message": "Server not found"},
            status_code=404
        )
    return JSONResponse(content=server)


@app.post("/invite-to-server")
async def invite_to_server_route(
    server_id: int = Form(...),
    user_id: int = Form(...),
    current_user: dict = Depends(get_current_user_required)
):
    """Invite a user to a server"""
    result = send_server_invite(server_id, current_user['id'], user_id)
    return JSONResponse(content=result)


@app.get("/server-invites")
async def get_server_invites_route(current_user: dict = Depends(get_current_user_required)):
    """Get pending server invites"""
    invites = get_pending_server_invites(current_user['id'])
    return JSONResponse(content={"invites": invites})


@app.post("/accept-server-invite")
async def accept_server_invite_route(
    invite_id: int = Form(...),
    current_user: dict = Depends(get_current_user_required)
):
    """Accept a server invitation"""
    result = accept_server_invite(invite_id, current_user['id'])
    return JSONResponse(content=result)


@app.post("/decline-server-invite")
async def decline_server_invite_route(
    invite_id: int = Form(...),
    current_user: dict = Depends(get_current_user_required)
):
    """Decline a server invitation"""
    result = decline_server_invite(invite_id, current_user['id'])
    return JSONResponse(content=result)


@app.post("/create-channel")
async def create_channel_route(
    server_id: int = Form(...),
    name: str = Form(...),
    current_user: dict = Depends(get_current_user_required)
):
    """Create a new channel in a server"""
    result = create_channel(server_id, name, current_user['id'])
    return JSONResponse(content=result)


@app.get("/server/{server_id}/channels")
async def get_server_channels_route(
    server_id: int,
    current_user: dict = Depends(get_current_user_required)
):
    """Get all channels in a server"""
    channels = get_server_channels(server_id)
    return JSONResponse(content={"channels": channels})


@app.post("/join-channel")
async def join_channel_route(
    channel_id: int = Form(...),
    current_user: dict = Depends(get_current_user_required)
):
    """Join a channel"""
    result = join_channel(channel_id, current_user['id'])
    return JSONResponse(content=result)


@app.post("/leave-channel")
async def leave_channel_route(
    channel_id: int = Form(...),
    current_user: dict = Depends(get_current_user_required)
):
    """Leave a channel"""
    result = leave_channel(channel_id, current_user['id'])
    return JSONResponse(content=result)


@app.get("/channel/{channel_id}/members")
async def get_channel_members_route(
    channel_id: int,
    current_user: dict = Depends(get_current_user_required)
):
    """Get all members in a channel"""
    members = get_channel_members(channel_id)
    return JSONResponse(content={"members": members})


@app.get("/channel/{channel_id}/messages")
async def get_channel_messages_route(
    channel_id: int,
    current_user: dict = Depends(get_current_user_required)
):
    """Get messages from a channel"""
    messages = get_channel_messages(channel_id)
    return JSONResponse(content={"messages": messages})


@app.post("/send-channel-message")
async def send_channel_message_route(
    request: Request,
    current_user: dict = Depends(get_current_user_required)
):
    """Send a message to a channel"""
    data = await request.json()
    channel_id = data.get('channel_id')
    message = data.get('message')
    
    if not channel_id or not message:
        return JSONResponse(
            content={"success": False, "message": "Missing channel_id or message"},
            status_code=400
        )
    
    result = save_channel_message(channel_id, current_user['id'], message)
    return JSONResponse(content=result)


# ============================================
# WEBSOCKET
# ============================================

async def get_websocket_user(websocket: WebSocket) -> Optional[dict]:
    """
    Authenticate WebSocket connection using session token from query params
    Returns user dict if authenticated, None otherwise
    """
    session_token = websocket.query_params.get("session")
    
    if not session_token:
        return None
    
    user_id = verify_session(session_token)
    if not user_id:
        return None
    
    return get_user_by_id(user_id)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint with proper authentication
    Rejects connection if user is not authenticated
    """
    # Authenticate before accepting connection
    user = await get_websocket_user(websocket)
    
    if not user:
        # Reject connection with close code
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Not authenticated")
        return
    
    # Accept connection only after authentication succeeds
    await websocket.accept()
    print(f"User {user['username']} (ID: {user['id']}) connected to WebSocket")
    
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from {user['username']}: {data}")
            # Broadcast back to the sender (echo) for now
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        print(f"User {user['username']} disconnected from WebSocket")
