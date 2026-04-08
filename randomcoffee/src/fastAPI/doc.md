# RandomCoffee API Endpoints

- POST /login_start(email:str) -> 200 {} / 421 {"error":"too many requests"}
- POST /login(email:str, otp:str) -> 200 {"jwt":"..."} / 401 {"detail":"Invalid credentials"}
- GET /myprofile(jwt:str) -> 200 {...} / 401 {"detail":"Unauthorized"}
- PATCH /myprofile(jwt:str, name?:str, contact_info?:str, is_active?:bool) -> 200 {} / 401 / 404
- GET /profile/{user_id} -> 200 {...} / 404 {"detail":"User not found"}
- GET /notifications(jwt:str, status?:"attended"|"not-attended"|"all", n?:int) -> 200 [{...},{...},...] / 401 / 403 / 400
- POST /confirm(jwt:str, notification_id:str) -> 200 {} / 401 / 403 / 404
- POST /admin/pairing(jwt:str, admin_required) -> 200 {} / 401 / 403
