# Pizza Striker Backend — Detailed Development Plan

## 1. Project Summary

**Pizza Striker** is a gamified office application where employees receive "strikes" for workplace goofs. When an employee accumulates **3 strikes**, they must host a **pizza party** for the team. This backend provides all the APIs for user management, strike tracking, pizza party events, and admin oversight.

- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (running in its own Docker container)
- **ORM**: SQLAlchemy 2.0 (async with `asyncpg`)
- **Migrations**: Alembic
- **Auth**: JWT-based authentication with role-based access control (RBAC)
- **Roles**: `admin`, `employee`
- **Containerization**: Docker Compose (separate containers for backend + database)

---

## 2. PostgreSQL Schema Design

PostgreSQL with SQLAlchemy 2.0 (async mode using `asyncpg`). Alembic handles migrations. Below is the full schema.

### 2.1 Table: `users`

Stores all registered users (both admins and employees).

| Field        | Type                     | Constraints                          | Description                    |
| ------------ | ------------------------ | ------------------------------------ | ------------------------------ |
| `id`         | INTEGER                  | PRIMARY KEY, AUTO INCREMENT          | Unique user ID                 |
| `name`       | VARCHAR(100)             | NOT NULL                             | Full name of the user          |
| `email`      | VARCHAR(255)             | NOT NULL, UNIQUE                     | Email address (used for login) |
| `password`   | VARCHAR(255)             | NOT NULL                             | Hashed password (bcrypt)       |
| `role`       | VARCHAR(20)              | NOT NULL, CHECK IN (admin, employee) | User role                      |
| `avatar_url` | VARCHAR(500)             | NULLABLE                             | Optional profile picture URL   |
| `department` | VARCHAR(100)             | NULLABLE                             | Optional department name       |
| `is_active`  | BOOLEAN                  | NOT NULL, DEFAULT TRUE               | Whether the account is active  |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW()              | Account creation timestamp     |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW()              | Last profile update timestamp  |

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'employee')),
    avatar_url VARCHAR(500),
    department VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

### 2.2 Table: `strikes`

Each row represents a single strike given to an employee.

| Field          | Type                     | Constraints                 | Description                                |
| -------------- | ------------------------ | --------------------------- | ------------------------------------------ |
| `id`           | INTEGER                  | PRIMARY KEY, AUTO INCREMENT | Unique strike ID                           |
| `user_id`      | INTEGER                  | NOT NULL, FK → users(id)    | The user who received the strike           |
| `given_by_id`  | INTEGER                  | NOT NULL, FK → users(id)    | The admin who issued it                    |
| `reason`       | TEXT                     | NOT NULL                    | Description of why the strike was given    |
| `category`     | VARCHAR(50)              | NOT NULL, CHECK constraint  | Category (late, bug, forgot_meeting, etc.) |
| `evidence_url` | VARCHAR(500)             | NULLABLE                    | Optional link to proof                     |
| `is_active`    | BOOLEAN                  | NOT NULL, DEFAULT TRUE      | Whether the strike is still valid          |
| `created_at`   | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW()     | When the strike was issued                 |

```sql
CREATE TABLE strikes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    given_by_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('late', 'bug', 'forgot_meeting', 'dress_code', 'other')),
    evidence_url VARCHAR(500),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_strikes_user_id ON strikes(user_id);
CREATE INDEX idx_strikes_given_by_id ON strikes(given_by_id);
CREATE INDEX idx_strikes_is_active ON strikes(is_active);
```

### 2.3 Table: `pizza_events`

Created automatically when a user reaches 3 active strikes.

| Field             | Type                     | Constraints                 | Description                                 |
| ----------------- | ------------------------ | --------------------------- | ------------------------------------------- |
| `id`              | INTEGER                  | PRIMARY KEY, AUTO INCREMENT | Unique event ID                             |
| `triggered_by_id` | INTEGER                  | NOT NULL, FK → users(id)    | The user who hit 3 strikes                  |
| `status`          | VARCHAR(20)              | NOT NULL, CHECK constraint  | pending / scheduled / completed / cancelled |
| `scheduled_date`  | TIMESTAMP WITH TIME ZONE | NULLABLE                    | When the pizza party is planned             |
| `notes`           | TEXT                     | NULLABLE                    | Admin notes                                 |
| `created_at`      | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW()     | When the event was auto-created             |
| `updated_at`      | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW()     | Last update timestamp                       |

```sql
CREATE TABLE pizza_events (
    id SERIAL PRIMARY KEY,
    triggered_by_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'scheduled', 'completed', 'cancelled')),
    scheduled_date TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pizza_events_triggered_by ON pizza_events(triggered_by_id);
CREATE INDEX idx_pizza_events_status ON pizza_events(status);
```

### 2.4 Table: `pizza_event_strikes` (Join Table)

Links the 3 strikes that triggered a pizza event (many-to-many relationship).

| Field            | Type    | Constraints                     | Description     |
| ---------------- | ------- | ------------------------------- | --------------- |
| `pizza_event_id` | INTEGER | NOT NULL, FK → pizza_events(id) | The pizza event |
| `strike_id`      | INTEGER | NOT NULL, FK → strikes(id)      | The strike      |

```sql
CREATE TABLE pizza_event_strikes (
    pizza_event_id INTEGER NOT NULL REFERENCES pizza_events(id) ON DELETE CASCADE,
    strike_id INTEGER NOT NULL REFERENCES strikes(id) ON DELETE CASCADE,
    PRIMARY KEY (pizza_event_id, strike_id)
);
```

### 2.5 Table: `notifications`

Stores notifications sent to users (e.g., "You received a strike", "Pizza party triggered!").

| Field        | Type                     | Constraints                 | Description                                                                |
| ------------ | ------------------------ | --------------------------- | -------------------------------------------------------------------------- |
| `id`         | INTEGER                  | PRIMARY KEY, AUTO INCREMENT | Unique notification ID                                                     |
| `user_id`    | INTEGER                  | NOT NULL, FK → users(id)    | The recipient user                                                         |
| `title`      | VARCHAR(200)             | NOT NULL                    | Short notification title                                                   |
| `message`    | TEXT                     | NOT NULL                    | Full notification message                                                  |
| `type`       | VARCHAR(50)              | NOT NULL                    | strike_received, strike_revoked, pizza_triggered, pizza_scheduled, general |
| `is_read`    | BOOLEAN                  | NOT NULL, DEFAULT FALSE     | Whether the user has read this notification                                |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW()     | When the notification was created                                          |

```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
```

### 2.6 Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐       ┌───────────────────────┐
│    users     │       │     strikes      │       │    pizza_events       │
├──────────────┤       ├──────────────────┤       ├───────────────────────┤
│ id (PK)      │◄──┐   │ id (PK)          │   ┌──►│ id (PK)               │
│ name         │   ├───│ user_id (FK)     │   │   │ triggered_by_id (FK)  │
│ email        │   │   │ given_by_id (FK) │───┘   │ status                │
│ password     │   │   │ reason           │       │ scheduled_date        │
│ role         │   │   │ category         │       │ notes                 │
│ avatar_url   │   │   │ evidence_url     │       │ created_at            │
│ department   │   │   │ is_active        │       │ updated_at            │
│ is_active    │   │   │ created_at       │       └───────────┬───────────┘
│ created_at   │   │   └──────────┬───────┘                   │
│ updated_at   │   │              │                           │
└──────┬───────┘   │              │     ┌─────────────────────┘
       │           │              │     │
       │           │              ▼     ▼
       │           │   ┌──────────────────────────┐
       │           │   │  pizza_event_strikes     │
       │           │   ├──────────────────────────┤
       │           │   │ pizza_event_id (FK, PK)  │
       │           │   │ strike_id (FK, PK)       │
       │           │   └──────────────────────────┘
       │           │
       │    ┌──────┘
       ▼    ▼
┌──────────────────┐
│  notifications   │
├──────────────────┤
│ id (PK)          │
│ user_id (FK)     │
│ title            │
│ message          │
│ type             │
│ is_read          │
│ created_at       │
└──────────────────┘
```

---

## 3. Authentication & Authorization

### 3.1 Auth Flow

1. User registers or is created by admin → password is hashed with **bcrypt**
2. User logs in with email + password → server validates credentials → returns **JWT access token** + **refresh token**
3. JWT contains: `user_id`, `role`, `exp` (expiry)
4. All protected endpoints require `Authorization: Bearer <token>` header
5. Middleware decodes JWT, attaches user info to request context

### 3.2 Role-Based Access Control (RBAC)

| Action                    | `admin` | `employee` |
| ------------------------- | ------- | ---------- |
| Register new users        | ✅      | ❌         |
| View all users            | ✅      | ❌         |
| View own profile          | ✅      | ✅         |
| Update own profile        | ✅      | ✅         |
| Add strikes to employees  | ✅      | ❌         |
| Revoke a strike           | ✅      | ❌         |
| View own strikes          | ✅      | ✅         |
| View all strikes          | ✅      | ❌         |
| View pizza events         | ✅      | ✅ (own)   |
| Update pizza event status | ✅      | ❌         |
| View own notifications    | ✅      | ✅         |
| View dashboard/stats      | ✅      | ❌         |

---

## 4. API Endpoints — Detailed Specification

All endpoints are prefixed with `/api/v1`.
All responses follow a consistent format:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... }
}
```

Error responses:

```json
{
  "success": false,
  "message": "Error description",
  "error_code": "VALIDATION_ERROR"
}
```

---

### 4.1 Auth Endpoints (`/api/v1/auth`)

These are **public** (no token required).

#### `POST /api/v1/auth/register`

Register a new user. Only admins can register other users (except for initial setup where first user becomes admin).

- **Request Body**:
  ```json
  {
    "name": "John Doe",
    "email": "john@company.com",
    "password": "securepassword123",
    "role": "employee",
    "department": "Engineering"
  }
  ```
- **Response** (201):
  ```json
  {
    "success": true,
    "message": "User registered successfully",
    "data": {
      "id": 1,
      "name": "John Doe",
      "email": "john@company.com",
      "role": "employee"
    }
  }
  ```
- **Errors**: 409 if email already exists, 422 if validation fails
- **Business Logic**: The very first user registered in the system is automatically assigned the `admin` role. All subsequent registrations require an admin JWT token and go through the admin endpoint.

#### `POST /api/v1/auth/login`

Authenticate and receive tokens.

- **Request Body**:
  ```json
  {
    "email": "john@company.com",
    "password": "securepassword123"
  }
  ```
- **Response** (200):
  ```json
  {
    "success": true,
    "message": "Login successful",
    "data": {
      "access_token": "eyJhbGci...",
      "refresh_token": "eyJhbGci...",
      "token_type": "bearer",
      "expires_in": 3600,
      "user": {
        "id": 1,
        "name": "John Doe",
        "role": "employee"
      }
    }
  }
  ```
- **Errors**: 401 if credentials are wrong, 403 if account is deactivated

#### `POST /api/v1/auth/refresh`

Get a new access token using a refresh token.

- **Request Body**:
  ```json
  {
    "refresh_token": "eyJhbGci..."
  }
  ```
- **Response** (200): Same as login response with new tokens
- **Errors**: 401 if refresh token is invalid or expired

#### `POST /api/v1/auth/logout`

Invalidate the current refresh token (server-side blacklist).

- **Headers**: `Authorization: Bearer <access_token>`
- **Response** (200): `{ "success": true, "message": "Logged out successfully" }`

---

### 4.2 User Endpoints (`/api/v1/users`)

All require authentication.

#### `GET /api/v1/users/me`

Get the current authenticated user's profile.

- **Access**: `admin`, `employee`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "id": 1,
      "name": "John Doe",
      "email": "john@company.com",
      "role": "employee",
      "department": "Engineering",
      "avatar_url": null,
      "is_active": true,
      "strike_count": 2,
      "created_at": "2026-04-20T10:00:00Z"
    }
  }
  ```
- **Note**: `strike_count` is computed at query time by counting active strikes for this user.

#### `PUT /api/v1/users/me`

Update the current user's own profile (name, avatar, department only — not role or email).

- **Access**: `admin`, `employee`
- **Request Body** (all fields optional):
  ```json
  {
    "name": "John D.",
    "avatar_url": "https://example.com/avatar.png",
    "department": "Product"
  }
  ```
- **Response** (200): Updated user object

#### `PUT /api/v1/users/me/password`

Change own password.

- **Access**: `admin`, `employee`
- **Request Body**:
  ```json
  {
    "current_password": "oldpassword",
    "new_password": "newpassword123"
  }
  ```
- **Response** (200): `{ "success": true, "message": "Password updated" }`
- **Errors**: 401 if current password is wrong

---

### 4.3 Strike Endpoints (`/api/v1/strikes`)

#### `GET /api/v1/strikes/me`

Get the current user's own strike history.

- **Access**: `admin`, `employee`
- **Query Params**:
  - `is_active` (optional, bool) — filter active/revoked strikes
  - `page` (int, default 1)
  - `limit` (int, default 20, max 100)
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "strikes": [
        {
          "id": 3,
          "reason": "Showed up late to standup",
          "category": "late",
          "given_by": {
            "id": 2,
            "name": "Admin Jane"
          },
          "is_active": true,
          "created_at": "2026-04-21T09:30:00Z"
        }
      ],
      "total": 2,
      "active_count": 2,
      "page": 1,
      "limit": 20
    }
  }
  ```

---

### 4.4 Notification Endpoints (`/api/v1/notifications`)

#### `GET /api/v1/notifications`

Get the current user's notifications.

- **Access**: `admin`, `employee`
- **Query Params**:
  - `is_read` (optional, bool) — filter read/unread
  - `page` (int, default 1)
  - `limit` (int, default 20)
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "notifications": [
        {
          "id": 1,
          "title": "Strike Received!",
          "message": "You received a strike for: Showed up late to standup",
          "type": "strike_received",
          "is_read": false,
          "created_at": "2026-04-21T09:30:00Z"
        }
      ],
      "unread_count": 3,
      "total": 5
    }
  }
  ```

#### `PUT /api/v1/notifications/{notification_id}/read`

Mark a notification as read.

- **Access**: `admin`, `employee` (own notifications only)
- **Response** (200): `{ "success": true, "message": "Notification marked as read" }`

#### `PUT /api/v1/notifications/read-all`

Mark all of the current user's notifications as read.

- **Access**: `admin`, `employee`
- **Response** (200): `{ "success": true, "message": "All notifications marked as read" }`

---

### 4.5 Pizza Event Endpoints — Employee View (`/api/v1/pizza-events`)

#### `GET /api/v1/pizza-events/me`

Get pizza events triggered by the current user.

- **Access**: `admin`, `employee`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "events": [
        {
          "id": 1,
          "status": "pending",
          "scheduled_date": null,
          "strike_count_at_trigger": 3,
          "created_at": "2026-04-22T10:00:00Z"
        }
      ]
    }
  }
  ```

---

## 5. Admin Panel API Endpoints

All admin endpoints require `role == "admin"`. Return 403 for non-admin users.

---

### 5.1 Admin — User Management (`/api/v1/admin/users`)

#### `GET /api/v1/admin/users`

List all users with filters and pagination.

- **Query Params**:
  - `role` (optional) — `"admin"` or `"employee"`
  - `department` (optional) — filter by department
  - `is_active` (optional, bool)
  - `search` (optional) — search by name or email (partial match)
  - `sort_by` (optional) — `"name"`, `"created_at"`, `"strike_count"` (default: `"created_at"`)
  - `order` (optional) — `"asc"` or `"desc"` (default: `"desc"`)
  - `page` (int, default 1)
  - `limit` (int, default 20, max 100)
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "users": [
        {
          "id": 1,
          "name": "John Doe",
          "email": "john@company.com",
          "role": "employee",
          "department": "Engineering",
          "is_active": true,
          "strike_count": 2,
          "created_at": "2026-04-20T10:00:00Z"
        }
      ],
      "total": 15,
      "page": 1,
      "limit": 20
    }
  }
  ```

#### `GET /api/v1/admin/users/{user_id}`

Get detailed profile of a specific user including their strike summary.

- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "id": 1,
      "name": "John Doe",
      "email": "john@company.com",
      "role": "employee",
      "department": "Engineering",
      "is_active": true,
      "avatar_url": null,
      "strike_count": 2,
      "total_strikes_ever": 5,
      "pizza_events_count": 1,
      "created_at": "2026-04-20T10:00:00Z",
      "updated_at": "2026-04-21T14:00:00Z"
    }
  }
  ```

#### `POST /api/v1/admin/users`

Create a new user (admin registers employees).

- **Request Body**:
  ```json
  {
    "name": "New Employee",
    "email": "new@company.com",
    "password": "temppassword123",
    "role": "employee",
    "department": "Marketing"
  }
  ```
- **Response** (201): Created user object
- **Business Logic**: A notification is sent to the new user with their credentials. Password must be changed on first login (optional enhancement).

#### `PUT /api/v1/admin/users/{user_id}`

Update any user's profile (admin can change role, department, active status).

- **Request Body** (all optional):
  ```json
  {
    "name": "Updated Name",
    "role": "admin",
    "department": "Engineering",
    "is_active": false
  }
  ```
- **Response** (200): Updated user object
- **Note**: Setting `is_active: false` effectively deactivates the user (they can't login).

#### `DELETE /api/v1/admin/users/{user_id}`

Soft-delete a user (sets `is_active` to false). Does NOT delete from DB.

- **Response** (200): `{ "success": true, "message": "User deactivated" }`
- **Business Logic**: Admin cannot deactivate themselves. System must always have at least one active admin.

---

### 5.2 Admin — Strike Management (`/api/v1/admin/strikes`)

#### `GET /api/v1/admin/strikes`

List all strikes across all users.

- **Query Params**:
  - `user_id` (optional) — filter by specific user
  - `given_by` (optional) — filter by admin who issued it
  - `category` (optional) — filter by strike category
  - `is_active` (optional, bool)
  - `date_from` (optional, ISO datetime)
  - `date_to` (optional, ISO datetime)
  - `sort_by` (optional) — `"created_at"`, `"category"` (default: `"created_at"`)
  - `order` (optional) — `"asc"` or `"desc"` (default: `"desc"`)
  - `page` (int, default 1)
  - `limit` (int, default 20, max 100)
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "strikes": [
        {
          "id": 3,
          "user": {
            "id": 1,
            "name": "John Doe"
          },
          "given_by": {
            "id": 2,
            "name": "Admin Jane"
          },
          "reason": "Showed up late to standup",
          "category": "late",
          "evidence_url": null,
          "is_active": true,
          "created_at": "2026-04-21T09:30:00Z"
        }
      ],
      "total": 42,
      "page": 1,
      "limit": 20
    }
  }
  ```

#### `GET /api/v1/admin/strikes/{strike_id}`

Get details of a specific strike.

- **Response** (200): Full strike object with expanded user and given_by fields.

#### `POST /api/v1/admin/strikes`

Issue a new strike to an employee. **This is the core action of the app.**

- **Request Body**:
  ```json
  {
    "user_id": 1,
    "reason": "Deployed to production on Friday at 5pm",
    "category": "bug",
    "evidence_url": "https://slack.com/archives/..."
  }
  ```
- **Response** (201):
  ```json
  {
    "success": true,
    "message": "Strike issued successfully",
    "data": {
      "strike": {
        "id": 7,
        "user": { "id": 1, "name": "John Doe" },
        "reason": "Deployed to production on Friday at 5pm",
        "category": "bug",
        "is_active": true,
        "created_at": "2026-04-22T10:00:00Z"
      },
      "user_active_strike_count": 3,
      "pizza_event_triggered": true
    }
  }
  ```
- **Business Logic** (CRITICAL — this is the core flow):
  1. Validate that the target user exists and is an active employee.
  2. Admin cannot strike themselves.
  3. Create the strike record in the `strike` table.
  4. Count the user's current **active** strikes.
  5. Create a notification for the user: "You received a strike for: {reason}".
  6. **If active strikes == 3**:
     a. Create a new `pizza_event` with status `"pending"`.
     b. Link the 3 active strike IDs to the event.
     c. Create a notification for the user: "🍕 You've hit 3 strikes! Time to order pizza for the team!"
     d. Create a notification for all admins: "🍕 {user.name} has triggered a pizza party!"
     e. Reset: Mark all 3 strikes as `is_active: false` (they've been "consumed" by the pizza event). This way the user starts fresh with 0 active strikes.
  7. Return the strike, updated count, and whether a pizza event was triggered.

#### `PUT /api/v1/admin/strikes/{strike_id}/revoke`

Revoke (cancel) a strike. Sets `is_active` to false.

- **Request Body** (optional):
  ```json
  {
    "reason": "Strike was given by mistake"
  }
  ```
- **Response** (200):
  ```json
  {
    "success": true,
    "message": "Strike revoked",
    "data": {
      "strike_id": 3,
      "user_active_strike_count": 1
    }
  }
  ```
- **Business Logic**: Create a notification for the user: "A strike has been revoked: {original_reason}". If this strike was part of a pending pizza event, the event should be marked as `"cancelled"`.

---

### 5.3 Admin — Pizza Event Management (`/api/v1/admin/pizza-events`)

#### `GET /api/v1/admin/pizza-events`

List all pizza party events.

- **Query Params**:
  - `status` (optional) — `"pending"`, `"scheduled"`, `"completed"`, `"cancelled"`
  - `triggered_by` (optional) — filter by user ID
  - `date_from` / `date_to` (optional)
  - `page` / `limit`
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "events": [
        {
          "id": 1,
          "triggered_by": {
            "id": 1,
            "name": "John Doe"
          },
          "status": "pending",
          "scheduled_date": null,
          "strikes": [
            {
              "id": 4,
              "reason": "Late to standup",
              "category": "late"
            },
            {
              "id": 5,
              "reason": "Broke the build",
              "category": "bug"
            },
            {
              "id": 6,
              "reason": "Forgot meeting",
              "category": "forgot_meeting"
            }
          ],
          "notes": null,
          "created_at": "2026-04-22T10:00:00Z"
        }
      ],
      "total": 3
    }
  }
  ```

#### `GET /api/v1/admin/pizza-events/{event_id}`

Get details of a specific pizza event.

#### `PUT /api/v1/admin/pizza-events/{event_id}`

Update a pizza event (schedule it, mark complete, add notes).

- **Request Body** (all optional):
  ```json
  {
    "status": "scheduled",
    "scheduled_date": "2026-04-30T12:00:00Z",
    "notes": "Pizza party at the office cafeteria. John is ordering from Dominos."
  }
  ```
- **Response** (200): Updated event object
- **Business Logic**:
  - When status changes to `"scheduled"`: Notify the triggering user and all employees: "Pizza party scheduled for {date}!"
  - When status changes to `"completed"`: Notify all: "Pizza party completed! Thanks {user.name}!"

---

### 5.4 Admin — Dashboard & Analytics (`/api/v1/admin/dashboard`)

#### `GET /api/v1/admin/dashboard/summary`

Get overall system statistics.

- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "total_users": 25,
      "active_users": 23,
      "total_admins": 3,
      "total_employees": 22,
      "total_strikes_issued": 87,
      "active_strikes": 15,
      "total_pizza_events": 12,
      "pending_pizza_events": 2,
      "completed_pizza_events": 9,
      "top_strike_categories": [
        { "category": "late", "count": 35 },
        { "category": "bug", "count": 28 },
        { "category": "forgot_meeting", "count": 15 }
      ]
    }
  }
  ```

#### `GET /api/v1/admin/dashboard/leaderboard`

Get the "strike leaderboard" — users ranked by active strike count.

- **Query Params**:
  - `type` (optional) — `"active"` (current active strikes) or `"all_time"` (total strikes ever). Default: `"active"`
  - `limit` (int, default 10)
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "leaderboard": [
        {
          "rank": 1,
          "user": {
            "id": 1,
            "name": "John Doe",
            "department": "Engineering"
          },
          "active_strikes": 2,
          "total_strikes": 8,
          "pizza_events": 2
        },
        {
          "rank": 2,
          "user": {
            "id": 3,
            "name": "Jane Smith",
            "department": "Marketing"
          },
          "active_strikes": 1,
          "total_strikes": 4,
          "pizza_events": 1
        }
      ]
    }
  }
  ```

#### `GET /api/v1/admin/dashboard/recent-activity`

Get a feed of recent actions (strikes given, events triggered, users registered).

- **Query Params**:
  - `limit` (int, default 20)
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "activities": [
        {
          "type": "strike_issued",
          "description": "Admin Jane gave John Doe a strike for: Late to standup",
          "timestamp": "2026-04-22T09:30:00Z"
        },
        {
          "type": "pizza_triggered",
          "description": "John Doe triggered a pizza party!",
          "timestamp": "2026-04-22T09:30:00Z"
        }
      ]
    }
  }
  ```

#### `GET /api/v1/admin/dashboard/strike-trends`

Get strike count trends over time (for charts).

- **Query Params**:
  - `period` (optional) — `"daily"`, `"weekly"`, `"monthly"` (default: `"weekly"`)
  - `range` (optional) — `"30d"`, `"90d"`, `"1y"` (default: `"30d"`)
- **Response** (200):
  ```json
  {
    "success": true,
    "data": {
      "period": "weekly",
      "trends": [
        { "date": "2026-04-15", "strikes": 5 },
        { "date": "2026-04-08", "strikes": 8 },
        { "date": "2026-04-01", "strikes": 3 }
      ]
    }
  }
  ```

---

## 6. Project Folder Structure

```
pizza_striker_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app initialization, CORS, lifespan
│   ├── config.py                # Settings from .env (DB URL, JWT secret, etc.)
│   ├── database.py              # SQLAlchemy async engine, sessionmaker, get_db dependency
│   ├── models.py                # SQLAlchemy ORM models (User, Strike, PizzaEvent, etc.)
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py            # Auth endpoints (login, register, refresh, logout)
│   │   ├── service.py           # Auth business logic (hash, verify, token creation)
│   │   ├── dependencies.py      # get_current_user, require_admin dependencies
│   │   └── schemas.py           # Pydantic models for auth requests/responses
│   │
│   ├── users/
│   │   ├── __init__.py
│   │   ├── router.py            # User endpoints (/users/me, etc.)
│   │   ├── service.py           # User CRUD operations against PostgreSQL
│   │   └── schemas.py           # Pydantic models for user data
│   │
│   ├── strikes/
│   │   ├── __init__.py
│   │   ├── router.py            # Strike endpoints (employee view: /strikes/me)
│   │   ├── service.py           # Strike CRUD + pizza trigger logic
│   │   └── schemas.py           # Pydantic models for strike data
│   │
│   ├── pizza_events/
│   │   ├── __init__.py
│   │   ├── router.py            # Pizza event endpoints (employee view)
│   │   ├── service.py           # Pizza event management logic
│   │   └── schemas.py           # Pydantic models for pizza event data
│   │
│   ├── notifications/
│   │   ├── __init__.py
│   │   ├── router.py            # Notification endpoints
│   │   ├── service.py           # Notification creation and retrieval
│   │   └── schemas.py           # Pydantic models for notifications
│   │
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── users_router.py      # Admin user management endpoints
│   │   ├── strikes_router.py    # Admin strike management endpoints
│   │   ├── events_router.py     # Admin pizza event management endpoints
│   │   ├── dashboard_router.py  # Admin dashboard/analytics endpoints
│   │   └── schemas.py           # Admin-specific Pydantic models
│   │
│   └── utils/
│       ├── __init__.py
│       ├── pagination.py        # Pagination helper (page/limit to offset)
│       └── responses.py         # Standard response format helpers
│
├── alembic/                         # Alembic migrations directory
│   ├── env.py                       # Migration environment config
│   ├── script.py.mako               # Migration script template
│   └── versions/                    # Auto-generated migration files
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Fixtures (test DB, test client, auth tokens)
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_strikes.py
│   ├── test_pizza_events.py
│   ├── test_notifications.py
│   └── test_admin_dashboard.py
│
├── .env                         # Environment variables (not committed)
├── .env.example                 # Example env file (committed)
├── .gitignore
├── alembic.ini                  # Alembic configuration
├── requirements.txt
├── Dockerfile                   # Backend container (Python + FastAPI)
├── docker-compose.yml           # Two containers: backend (app) + database (postgres)
├── README.md
└── PLAN.md                      # This file
```

---

## 7. Environment Variables (`.env`)

```env
# PostgreSQL
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=pizza_admin
POSTGRES_PASSWORD=pizza_secret_123
POSTGRES_DB=pizza_striker
DATABASE_URL=postgresql+asyncpg://pizza_admin:pizza_secret_123@db:5432/pizza_striker

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# App
APP_ENV=development
APP_DEBUG=true
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

> **Note**: When running outside Docker (local dev), change `db` to `localhost` in `DATABASE_URL`.
> Local dev URL: `postgresql+asyncpg://pizza_admin:pizza_secret_123@localhost:5432/pizza_striker`

---

## 8. Key Business Logic Rules

1. **Strike Limit**: When a user reaches **3 active strikes**, a pizza event is triggered automatically.
2. **Strike Reset**: After a pizza event is triggered, the 3 strikes that caused it are marked inactive. The user starts fresh at 0 active strikes.
3. **Strike Revocation**: An admin can revoke a strike at any time. If the strike was part of a pending (not yet completed) pizza event, that event is cancelled.
4. **First User = Admin**: The first user to register becomes an admin automatically. All subsequent users require admin creation.
5. **Self-Strike Prevention**: Admins cannot issue strikes to themselves.
6. **Admin Protection**: The system must always have at least 1 active admin. The last active admin cannot be deactivated.
7. **Soft Deletes**: Users are never hard-deleted. Deactivation (`is_active: false`) prevents login but preserves history.
8. **Notifications**: Every significant action creates a notification for the relevant user(s).

---

## 9. API Endpoint Summary Table

| Method | Endpoint                                  | Access   | Description                    |
| ------ | ----------------------------------------- | -------- | ------------------------------ |
| POST   | `/api/v1/auth/register`                   | Public\* | Register (first user) or Admin |
| POST   | `/api/v1/auth/login`                      | Public   | Login, get JWT tokens          |
| POST   | `/api/v1/auth/refresh`                    | Public   | Refresh access token           |
| POST   | `/api/v1/auth/logout`                     | Auth     | Invalidate refresh token       |
| GET    | `/api/v1/users/me`                        | Auth     | Get own profile                |
| PUT    | `/api/v1/users/me`                        | Auth     | Update own profile             |
| PUT    | `/api/v1/users/me/password`               | Auth     | Change own password            |
| GET    | `/api/v1/strikes/me`                      | Auth     | Get own strikes                |
| GET    | `/api/v1/notifications`                   | Auth     | Get own notifications          |
| PUT    | `/api/v1/notifications/{id}/read`         | Auth     | Mark notification as read      |
| PUT    | `/api/v1/notifications/read-all`          | Auth     | Mark all notifications as read |
| GET    | `/api/v1/pizza-events/me`                 | Auth     | Get own pizza events           |
| GET    | `/api/v1/admin/users`                     | Admin    | List all users                 |
| GET    | `/api/v1/admin/users/{id}`                | Admin    | Get user details               |
| POST   | `/api/v1/admin/users`                     | Admin    | Create new user                |
| PUT    | `/api/v1/admin/users/{id}`                | Admin    | Update user                    |
| DELETE | `/api/v1/admin/users/{id}`                | Admin    | Deactivate user                |
| GET    | `/api/v1/admin/strikes`                   | Admin    | List all strikes               |
| GET    | `/api/v1/admin/strikes/{id}`              | Admin    | Get strike details             |
| POST   | `/api/v1/admin/strikes`                   | Admin    | Issue a strike                 |
| PUT    | `/api/v1/admin/strikes/{id}/revoke`       | Admin    | Revoke a strike                |
| GET    | `/api/v1/admin/pizza-events`              | Admin    | List all pizza events          |
| GET    | `/api/v1/admin/pizza-events/{id}`         | Admin    | Get pizza event details        |
| PUT    | `/api/v1/admin/pizza-events/{id}`         | Admin    | Update pizza event             |
| GET    | `/api/v1/admin/dashboard/summary`         | Admin    | System statistics              |
| GET    | `/api/v1/admin/dashboard/leaderboard`     | Admin    | Strike leaderboard             |
| GET    | `/api/v1/admin/dashboard/recent-activity` | Admin    | Recent activity feed           |
| GET    | `/api/v1/admin/dashboard/strike-trends`   | Admin    | Strike trends over time        |

**Total: 27 endpoints**

---

## 10. Dependencies (`requirements.txt`)

```
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
alembic>=1.13.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-dotenv>=1.0.0
pydantic[email]>=2.0.0
pydantic-settings>=2.0.0
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

---

## 11. Docker Compose Setup

```yaml
version: "3.8"

services:
  # ── PostgreSQL Database Container ──────────────────────────────────
  db:
    image: postgres:16-alpine
    container_name: pizza_striker_db
    restart: unless-stopped
    environment:
      POSTGRES_USER: pizza_admin
      POSTGRES_PASSWORD: pizza_secret_123
      POSTGRES_DB: pizza_striker
    ports:
      - "5432:5432" # Exposed so you can connect locally with pgAdmin/psql
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pizza_admin -d pizza_striker"]
      interval: 5s
      timeout: 5s
      retries: 5

  # ── FastAPI Backend Container ──────────────────────────────────────
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: pizza_striker_app
    restart: unless-stopped
    ports:
      - "8080:8080"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy # Wait for Postgres to be ready
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8080"

volumes:
  postgres_data: # Named volume for persistent DB storage
```

### 11.1 Dockerfile (Backend)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 11.2 Running the Project

```bash
# Start both containers (first time builds the app image)
docker-compose up --build

# Run in background
docker-compose up --build -d

# View logs
docker-compose logs -f app
docker-compose logs -f db

# Stop everything
docker-compose down

# Stop and delete all data (fresh start)
docker-compose down -v
```

### 11.3 Connecting to the Database

```bash
# Via psql from host machine
psql -h localhost -p 5432 -U pizza_admin -d pizza_striker

# Via Docker exec
docker exec -it pizza_striker_db psql -U pizza_admin -d pizza_striker
```

---

## 12. Implementation Order (Recommended)

1. **Phase 1 — Foundation**
   - Project setup (FastAPI, SQLAlchemy async engine, config)
   - Docker Compose for PostgreSQL + backend containers
   - Alembic init + first migration (all tables)
   - SQLAlchemy ORM models
   - Standard response format utilities

2. **Phase 2 — Auth**
   - Register (first user = admin logic)
   - Login (JWT generation)
   - Token refresh & logout
   - Auth middleware (get_current_user, require_admin)

3. **Phase 3 — User Management**
   - Employee endpoints (GET/PUT own profile, change password)
   - Admin user CRUD

4. **Phase 4 — Strike System (Core Feature)**
   - Admin: issue strike
   - Pizza party trigger logic (3 strikes → event creation → strike reset)
   - Admin: revoke strike
   - Employee: view own strikes
   - Admin: list/filter all strikes

5. **Phase 5 — Pizza Events**
   - Auto-creation (from Phase 4)
   - Admin: list, update status, schedule
   - Employee: view own events

6. **Phase 6 — Notifications**
   - Notification creation (called from strike/event services)
   - User: list, mark read

7. **Phase 7 — Dashboard**
   - Summary stats
   - Leaderboard
   - Recent activity
   - Strike trends

8. **Phase 8 — Polish**
   - Tests
   - Docker setup
   - Documentation
   - Error handling refinement
