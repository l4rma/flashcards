from fastapi import HTTPException, Request

# No local-dev branch: there is no local/Docker deployment target for this
# app anymore, only the AWS one. API Gateway's Cognito JWT authorizer
# verifies the token (signature/issuer/expiry/audience) before Lambda is
# ever invoked, so this function only *reads* the already-verified `sub`
# claim off the raw Lambda event Mangum places in the ASGI scope — it does
# no cryptographic verification itself. Tests never exercise this real
# implementation; they override this dependency with a fixed test user id.


def get_current_user_id(request: Request) -> str:
    try:
        claims = request.scope["aws.event"]["requestContext"]["authorizer"]["jwt"]["claims"]
    except KeyError as exc:
        raise HTTPException(status_code=401, detail="Missing authentication") from exc
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Missing authentication")
    return sub
