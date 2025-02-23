import asyncio
from token_service import TokenService

async def delete_user_token(user_id: str):
    token_service = TokenService()
    success = await token_service.delete_token(user_id)
    if success:
        print(f"Successfully deleted token for user {user_id}")
    else:
        print(f"Failed to delete token for user {user_id}")

if __name__ == "__main__":
    USER_ID = "106573671377678694423"
    asyncio.run(delete_user_token(USER_ID)) 