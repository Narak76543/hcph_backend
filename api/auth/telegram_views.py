# TELEGRAM LOGIN - api/auth/telegram_views.py
from fastapi import Depends, HTTPException, Body, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from core.app import app
from core.db import get_db
from core.security import create_access_token, hash_password
from api.users.models import User, AuthProvider, UserRole
from api.users.schemas import TokenResponse
from utils.telegram_verify import verify_telegram_hash
import re
import os

# Bot token should be set as an environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

@app.post("/auth/telegram", response_model=TokenResponse, tags=["Auth"])
def telegram_login(data: dict = Body(...), db: Session = Depends(get_db)):
    """
    Authenticate a user using data from Telegram Login Widget.
    """
    print(f"DEBUG: Received telegram_login request with data: {data}")
    # 1. Verify Telegram Hash
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(500, "Telegram Bot Token is not configured on the server")
        
    if not verify_telegram_hash(data.copy(), TELEGRAM_BOT_TOKEN):
        raise HTTPException(401, "Invalid Telegram authentication data")
    
    telegram_id = int(data['id'])
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')
    telegram_username = data.get('username')
    photo_url = data.get('photo_url')

    # 2. Upsert User (Find by Telegram ID)
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if user:
        # Update existing user info
        user.firstname = first_name
        user.lastname = last_name
        user.telegram_username = telegram_username
        user.profile_image_url = photo_url
        user.auth_provider = AuthProvider.TELEGRAM
    else:
        # Create new user
        # Auto-generate unique username if not provided
        if telegram_username:
            username = telegram_username
            # Double check uniqueness in our DB
            if db.query(User).filter(User.username == username).first():
                username = f"{username}_{str(telegram_id)[-4:]}"
        else:
            # Generate from first name, stripping special chars
            base = re.sub(r'[^a-z0-9]', '', first_name.lower())
            if not base:
                base = "user"
            username = base
            counter = 1
            # Ensure uniqueness
            while db.query(User).filter(User.username == username).first():
                username = f"{base}{counter}"
                counter += 1
        
        # Provide placeholders for required database fields
        placeholder_email = f"tg_{telegram_id}@telegram.com"
        placeholder_phone = f"TG_{telegram_id}"
        placeholder_pwd   = hash_password(f"TELEGRAM_AUTH_{telegram_id}") # Dummy hash
        
        user = User(
            telegram_id       = telegram_id,
            firstname         = first_name,
            lastname          = last_name,
            firstname_lc      = first_name.lower(),
            lastname_lc       = last_name.lower(),
            username          = username,
            email             = placeholder_email,
            phone_number      = placeholder_phone,
            password_hash     = placeholder_pwd,
            telegram_username = telegram_username,
            profile_image_url = photo_url,
            auth_provider     = AuthProvider.TELEGRAM, 
            role              = UserRole.USER,         
            is_verified       = True
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    
    # 3. Generate Access Token
    token = create_access_token({"sub": str(user.id), "role": user.role})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@app.get("/auth/telegram/callback", response_class=HTMLResponse, tags=["Auth"])
@app.get("/auth/telegram/callback/", response_class=HTMLResponse, include_in_schema=False)
async def telegram_callback(request: Request):
    """
    Catch redirect from Telegram. Handles both query parameters (server-side)
    and URL fragments (client-side via JS) for maximum reliability.
    """
    print("DEBUG: telegram_callback [VERSION 3] called")
    params = dict(request.query_params)
    
    # Option A: Telegram sent query parameters (id, hash, etc.)
    if params:
        print(f"DEBUG: Redirecting via query params: {params.keys()}")
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return RedirectResponse(url=f"myapp://telegram-auth?{query_string}")

    # Option B: Telegram sent a fragment (#tgAuthResult=...)
    print("DEBUG: No query params found, returning JS fragment handler")
    return """
    <html>
        <head>
            <title>Redirecting...</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="background-color:#121212; color:white; display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; font-family:sans-serif; margin:0; padding:20px; text-align:center;">
            <div id="loading">
                <h2 id="status">Completing Login...</h2>
                <p>Please wait, returning to app.</p>
                <div style="margin:20px auto; width:40px; height:40px; border:4px solid #333; border-top:4px solid #229ED9; border-radius:50%; animation: spin 1s linear infinite;"></div>
            </div>

            <a id="fallback-btn" href="#" style="display:none; margin-top:20px; padding:12px 24px; background-color:#229ED9; color:white; text-decoration:none; border-radius:8px; font-weight:bold; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
                Back to App
            </a>

            <style>
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>

            <script>
                const hash = window.location.hash;
                const btn = document.getElementById('fallback-btn');
                
                if (hash && hash.includes('tgAuthResult=')) {
                    try {
                        const base64Data = hash.split('tgAuthResult=')[1];
                        const data = JSON.parse(atob(base64Data));
                        const query = new URLSearchParams(data).toString();
                        const deepLink = "myapp://telegram-auth?" + query;
                        
                        // Set the button link for fallback
                        btn.href = deepLink;
                        
                        // Try automatic redirect
                        window.location.href = deepLink;
                        
                        // Show button if we are still here after 1.5 seconds
                        setTimeout(() => {
                            btn.style.display = 'inline-block';
                            document.getElementById('status').innerText = "Redirect taking too long?";
                        }, 1500);

                    } catch (e) {
                        console.error("Failed to parse tgAuthResult", e);
                        document.body.innerHTML = "<h2 style='color:#ff4444'>Error processing login result.</h2>";
                    }
                } else {
                    document.body.innerHTML = "<h2>No login data detected.</h2>";
                }
            </script>
        </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse, tags=["Root"])
@app.get("", response_class=HTMLResponse, include_in_schema=False)
async def root():
    """
    Root route that handles the Telegram #tgAuthResult fragment and 
    redirects the user back to the Flutter app.
    """
    print("!!!!!!!!!! DEBUG: ROOT ROUTE HIT !!!!!!!!!!!")
    return """
    <html>
        <head><title>Authenticating...</title></head>
        <body style="display:flex; flex-direction:column; align-items:center; justify-content:center; height:100vh; font-family:sans-serif; background-color:#121212; color:white; margin:0; padding:20px; text-align:center;">
            <h2 id="status">Verifying Telegram Login...</h2>
            <p>Please wait, you will be redirected back to the app shortly.</p>
            <div style="margin-top:20px; width:40px; height:40px; border:4px solid #f3f3f3; border-top:4px solid #229ED9; border-radius:50%; animation: spin 1s linear infinite;"></div>
            
            <style>
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            </style>

            <script>
                // 1. Check if there is a telegram result in the URL fragment (#)
                const hash = window.location.hash;
                if (hash && hash.includes('tgAuthResult=')) {
                    try {
                        // 2. Extract the Base64 data
                        const base64Data = hash.split('tgAuthResult=')[1];
                        // 3. Decode it (Base64 -> JSON string -> Object)
                        const jsonStr = atob(base64Data);
                        const data = JSON.parse(jsonStr);
                        
                        // 4. Build the deep link for the Flutter app
                        const query = new URLSearchParams(data).toString();
                        const deepLink = "myapp://telegram-auth?" + query;
                        
                        document.getElementById('status').innerText = "Success! Redirecting...";
                        
                        // 5. Redirect to the app
                        window.location.href = deepLink;
                        
                        // Fallback if redirect doesn't trigger automatically
                        setTimeout(() => {
                            window.location.href = deepLink;
                        }, 1000);
                    } catch (e) {
                        document.getElementById('status').innerText = "Error processing login data.";
                        console.error(e);
                    }
                } else {
                    document.getElementById('status').innerText = "HCPH Backend is running.";
                }
            </script>
        </body>
    </html>
    """
