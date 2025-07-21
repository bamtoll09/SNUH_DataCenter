from pydantic import BaseModel

# @app.post("/loogin")
# async def loggg(
#     loginForm: LoginForm):
#     return "Good Job!"

class LoginForm(BaseModel):
    id: str
    pw: str

    # Request Example Value
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "test",
                    "pw": "admin",
                }
            ]
        }
    }