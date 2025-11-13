# Login System Documentation
# ระบบเข้าสู่ระบบ

## Overview / ภาพรวม

The Fabric Roll Management System now includes a secure login system with role-based access control. The system supports two user roles: **Admin** and **User**.

ระบบจัดการม้วนผ้าได้เพิ่มระบบเข้าสู่ระบบที่ปลอดภัยพร้อมการควบคุมสิทธิ์ตามบทบาท รองรับ 2 บทบาท: **ผู้ดูแลระบบ** และ **ผู้ใช้**

## User Roles / บทบาทผู้ใช้

### Admin (ผู้ดูแลระบบ)
**Full access to all features:**
- ✅ Access to Master Data tab
- ✅ Manage users (add, delete, reset passwords)
- ✅ All regular user features

**สิทธิ์เข้าถึงทุกฟีเจอร์:**
- ✅ เข้าถึงแท็บ Master Data
- ✅ จัดการผู้ใช้ (เพิ่ม, ลบ, รีเซ็ตรหัสผ่าน)
- ✅ ฟีเจอร์ผู้ใช้ทั่วไปทั้งหมด

### User (ผู้ใช้)
**Limited access:**
- ✅ Dashboard
- ✅ Receive / รับเข้า
- ✅ Rolls / จัดการม้วน
- ✅ Dispatch / เบิกออก
- ✅ Logs
- ✅ Reports / รายงาน
- ❌ **Cannot access Master Data tab**

**สิทธิ์จำกัด:**
- ✅ แดชบอร์ด
- ✅ รับเข้า
- ✅ จัดการม้วน
- ✅ เบิกออก
- ✅ บันทึก
- ✅ รายงาน
- ❌ **ไม่สามารถเข้าถึงแท็บ Master Data**

## Default Credentials / บัญชีเริ่มต้น

When you run the application for the first time, a default admin account is automatically created:

เมื่อเปิดโปรแกรมครั้งแรก บัญชีผู้ดูแลระบบเริ่มต้นจะถูกสร้างอัตโนมัติ:

```
Username: admin
Password: admin
```

**⚠️ IMPORTANT: Please change the default password immediately after first login!**

**⚠️ สำคัญ: กรุณาเปลี่ยนรหัสผ่านเริ่มต้นทันทีหลังจากเข้าสู่ระบบครั้งแรก!**

## Login Process / ขั้นตอนการเข้าสู่ระบบ

1. **Launch Application / เปิดโปรแกรม**
   - Run `main.py` or double-click the application executable
   - เรียกใช้ `main.py` หรือดับเบิลคลิกไฟล์โปรแกรม

2. **Enter Credentials / กรอกข้อมูล**
   - Enter your username and password
   - กรอกชื่อผู้ใช้และรหัสผ่าน
   - Optionally check "Show password" to reveal password
   - สามารถเลือก "แสดงรหัสผ่าน" เพื่อแสดงรหัสผ่าน

3. **Click Login / คลิกเข้าสู่ระบบ**
   - System will verify credentials
   - ระบบจะตรวจสอบข้อมูล
   - On success, you'll see a welcome message with your role
   - หากสำเร็จ จะแสดงข้อความต้อนรับพร้อมบทบาทของคุณ

4. **Access Application / เข้าใช้งานโปรแกรม**
   - Main window opens with tabs based on your role
   - หน้าต่างหลักจะเปิดพร้อมแท็บตามบทบาทของคุณ

## User Management (Admin Only) / การจัดการผู้ใช้ (สำหรับ Admin เท่านั้น)

### Adding New Users / เพิ่มผู้ใช้ใหม่

1. Go to **User → Manage Users**
   - ไปที่ **User → Manage Users**

2. Click **Add User / เพิ่มผู้ใช้**

3. Fill in the form:
   - **Username**: Unique username (required)
   - **Full Name**: Display name (required)
   - **Password**: Password for the user (required, minimum 4 characters)
   - **Role**: Select "admin" or "user"

4. Click **OK** to create the user

### Deleting Users / ลบผู้ใช้

1. Go to **User → Manage Users**
2. Select the user from the table
3. Click **Delete User / ลบผู้ใช้**
4. Confirm deletion

**Note:** You cannot delete yourself / คุณไม่สามารถลบตัวเองได้

### Resetting User Passwords / รีเซ็ตรหัสผ่านผู้ใช้

1. Go to **User → Manage Users**
2. Select the user from the table
3. Click **Reset Password / รีเซ็ตรหัสผ่าน**
4. Enter new password (minimum 4 characters)
5. Click **OK**

## Changing Your Password / เปลี่ยนรหัสผ่านของคุณ

1. Go to **User → Change Password**
   - ไปที่ **User → Change Password**

2. Fill in the form:
   - **Current Password**: Your current password
   - **New Password**: Your new password (minimum 4 characters)
   - **Confirm**: Re-enter new password

3. Click **OK** to change password

## Logging Out / ออกจากระบบ

1. Go to **User → Logout** or press **Ctrl+L**
   - ไปที่ **User → Logout** หรือกด **Ctrl+L**

2. Confirm logout

3. Application will close and return to login screen
   - โปรแกรมจะปิดและกลับไปหน้าเข้าสู่ระบบ

## Security Features / ฟีเจอร์ความปลอดภัย

- ✅ **Password Hashing**: Passwords are hashed using SHA-256
  - รหัสผ่านถูกเข้ารหัสด้วย SHA-256

- ✅ **Role-Based Access Control**: Features restricted by user role
  - การควบคุมสิทธิ์ตามบทบาท

- ✅ **Session Management**: Login session tracked per user
  - การจัดการเซสชั่นการเข้าสู่ระบบ

- ✅ **Last Login Tracking**: System tracks last login time for each user
  - ติดตามเวลาเข้าสู่ระบบล่าสุด

## File Structure / โครงสร้างไฟล์

```
Roll ID/
├── auth.py                      # Authentication manager module
├── data/
│   └── users.json              # User database (auto-created)
├── gui/
│   ├── main_window.py          # Main window (role-based UI)
│   └── dialogs/
│       └── login_dialog.py     # Login dialog
└── main.py                     # Application entry point
```

## Troubleshooting / แก้ไขปัญหา

### Cannot Login / เข้าสู่ระบบไม่ได้

1. **Check default credentials**: Try `admin` / `admin`
   - ตรวจสอบบัญชีเริ่มต้น: ลอง `admin` / `admin`

2. **Check users.json**: Look in `data/users.json` for user list
   - ตรวจสอบ users.json: ดูใน `data/users.json` สำหรับรายการผู้ใช้

3. **Reset users.json**: Delete the file to recreate default admin
   - รีเซ็ต users.json: ลบไฟล์เพื่อสร้างผู้ดูแลระบบเริ่มต้นใหม่

### Master Data Tab Not Visible / ไม่เห็นแท็บ Master Data

- This is expected behavior for **User** role
  - นี่คือพฤติกรรมปกติสำหรับบทบาท **ผู้ใช้**
- Only **Admin** users can access Master Data
  - เฉพาะ **ผู้ดูแลระบบ** เท่านั้นที่เข้าถึง Master Data ได้

### Forgot Password / ลืมรหัสผ่าน

1. **For Admins**: Delete `data/users.json` to reset to default admin
   - สำหรับผู้ดูแลระบบ: ลบ `data/users.json` เพื่อรีเซ็ตเป็นผู้ดูแลระบบเริ่มต้น

2. **For Users**: Contact an admin to reset your password
   - สำหรับผู้ใช้: ติดต่อผู้ดูแลระบบเพื่อรีเซ็ตรหัสผ่าน

## Best Practices / แนวทางปฏิบัติที่ดี

1. **Change default password immediately**
   - เปลี่ยนรหัสผ่านเริ่มต้นทันที

2. **Use strong passwords** (minimum 8 characters recommended)
   - ใช้รหัสผ่านที่แข็งแรง (แนะนำอย่างน้อย 8 ตัวอักษร)

3. **Create separate admin accounts** for different administrators
   - สร้างบัญชีผู้ดูแลระบบแยกสำหรับผู้ดูแลแต่ละคน

4. **Regularly review user list** and remove unused accounts
   - ตรวจสอบรายการผู้ใช้เป็นประจำและลบบัญชีที่ไม่ใช้งาน

5. **Backup users.json** regularly
   - สำรองข้อมูล users.json เป็นประจำ

## Technical Details / รายละเอียดทางเทคนิค

### Password Hashing
- Algorithm: SHA-256
- Format: Hexadecimal digest
- Salt: Not implemented (consider adding for production)

### User Database
- Format: JSON
- Location: `data/users.json`
- Encoding: UTF-8

### Session Management
- Type: In-memory session
- Duration: Until logout or application close
- Tracking: Last login timestamp

## Support / การสนับสนุน

For issues or questions about the login system, please contact your system administrator.

สำหรับปัญหาหรือคำถามเกี่ยวกับระบบเข้าสู่ระบบ กรุณาติดต่อผู้ดูแลระบบ
