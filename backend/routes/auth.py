from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.models.models import Organization, User
from backend.schemas.schemas import OrganizationCreate, OrganizationJoin, UserLogin, TokenResponse, UserResponse, OrganizationResponse
from backend.utils.security import hash_password, verify_password, create_access_token, generate_invite_code
from backend.auth.auth_handler import get_current_user, admin_required
from backend.schemas.schemas import OrganizationUpdate

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def _build_token_response(user: User, org: Organization) -> dict:
    token = create_access_token({
        "user_id": user.id,
        "organization_id": user.organization_id,
        "role": user.role
    })
    return {"access_token": token, "token_type": "bearer", "user": user, "organization": org}


@router.post("/create-workspace", response_model=TokenResponse)
def create_workspace(data: OrganizationCreate, db: Session = Depends(get_db)):
    """Admin creates a brand new workspace/organization."""
    # Ensure workspace_code is unique
    if db.query(Organization).filter(Organization.workspace_code == data.workspace_code).first():
        raise HTTPException(status_code=400, detail="Workspace code already taken. Please choose another.")

    # Generate a unique invite code
    invite_code = generate_invite_code(6)
    while db.query(Organization).filter(Organization.invite_code == invite_code).first():
        invite_code = generate_invite_code(6)

    # Create organization
    org = Organization(
        name=data.organization_name,
        type=data.organization_type,
        workspace_code=data.workspace_code.lower(),
        invite_code=invite_code,
        logo_url=data.logo_url,
        description=data.description
    )
    db.add(org)
    db.commit()
    db.refresh(org)

    # Create admin user
    # Ensure email not already used in this org (unlikely since org just created)
    admin_user = User(
        organization_id=org.id,
        name=data.admin_name,
        email=data.admin_email,
        password_hash=hash_password(data.admin_password),
        role="admin"
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return _build_token_response(admin_user, org)


@router.post("/join-workspace", response_model=TokenResponse)
def join_workspace(data: OrganizationJoin, db: Session = Depends(get_db)):
    """Student or Moderator joins an existing workspace using workspace_code + invite_code."""
    org = db.query(Organization).filter(
        Organization.workspace_code == data.workspace_code.lower()
    ).first()
    if not org:
        raise HTTPException(status_code=400, detail="Workspace not found. Check your workspace code.")

    if org.invite_code != data.invite_code.upper():
        raise HTTPException(status_code=400, detail="Invalid invite code. Please ask your administrator.")

    # Ensure email is unique within this org
    existing = db.query(User).filter(
        User.organization_id == org.id,
        User.email == data.email
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered in this workspace.")

    new_user = User(
        organization_id=org.id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="student"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return _build_token_response(new_user, org)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login using workspace_code + email + password."""
    org = db.query(Organization).filter(
        Organization.workspace_code == data.workspace_code.lower()
    ).first()
    if not org:
        raise HTTPException(status_code=401, detail="Workspace not found.")

    user = db.query(User).filter(
        User.organization_id == org.id,
        User.email == data.email
    ).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return _build_token_response(user, org)


@router.get("/me", response_model=TokenResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    return _build_token_response(current_user, org)


@router.put("/organization/settings", response_model=OrganizationResponse)
def update_organization_settings(
    data: OrganizationUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(admin_required)
):
    """Admin updates organization branding and settings."""
    org = db.query(Organization).filter(Organization.id == admin_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    if data.organization_name is not None:
        org.name = data.organization_name
    if data.organization_type is not None:
        org.type = data.organization_type
    if data.logo_url is not None:
        org.logo_url = data.logo_url
    if data.description is not None:
        org.description = data.description

    db.commit()
    db.refresh(org)
    return org


@router.post("/organization/regenerate-invite", response_model=OrganizationResponse)
def regenerate_invite_code(
    db: Session = Depends(get_db),
    admin_user: User = Depends(admin_required)
):
    """Admin regenerates the invite code for their workspace."""
    org = db.query(Organization).filter(Organization.id == admin_user.organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found.")

    new_code = generate_invite_code(6)
    while db.query(Organization).filter(Organization.invite_code == new_code).first():
        new_code = generate_invite_code(6)

    org.invite_code = new_code
    db.commit()
    db.refresh(org)
    return org


@router.get("/users", response_model=list)
def list_workspace_users(
    db: Session = Depends(get_db),
    admin_user: User = Depends(admin_required)
):
    """Admin lists all users in their workspace."""
    users = db.query(User).filter(User.organization_id == admin_user.organization_id).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "created_at": u.created_at} for u in users]
