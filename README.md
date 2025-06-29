# Reselling Platform API

Welcome to the Reselling Platform API! This project provides a robust backend for a gadget reselling platform, built with FastAPI. It handles gadget listings, admin management, buyer inquiries, and more.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup](#setup)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Database Initialization](#database-initialization)
  - [Creating an Admin User](#creating-an-admin-user)
- [API Endpoints](#api-endpoints)
  - [Seller Endpoints](#seller-endpoints)
  - [Buyer Endpoints](#buyer-endpoints)
  - [Admin Endpoints](#admin-endpoints)
  - [Public Endpoints](#public-endpoints)
- [Authentication](#authentication)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Gadget Listing Management:** Sellers can submit gadgets for listing, and administrators can manage, approve, update, and soft-delete listings.
- **Admin Dashboard:** Comprehensive dashboard for administrators to view pending, active, and sold listings, as well as buyer questions and gadget requests.
- **Buyer Interaction:** Buyers can submit questions about listings and request specific gadgets.
- **Public Listings:** Publicly accessible API for browsing available gadgets with filtering options.
- **Image Uploads:** Secure handling of gadget photos.
- **Admin Authentication:** Secure JWT-based authentication for administrators.
- **Settings Management:** Administrators can configure platform settings, such as a WhatsApp contact number for buyers.

## Tech Stack

- **Framework:** FastAPI
- **Database:** SQLite (via SQLAlchemy ORM)
- **Password Hashing:** Passlib (Bcrypt)
- **Authentication:** PyJWT (JSON Web Tokens)
- **File Uploads:** Python-Multipart
- **Testing:** Pytest, HTTpx

## Setup

### Prerequisites

- Python 3.9+
- `pip` (Python package installer)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/aqdev-tech/resell-api.git
    cd Wrap
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Database Initialization

The database schema will be automatically created when the application starts for the first time. A migration script `mig.py` is included for potential future schema changes (e.g., adding new columns).

To run the migration (if needed):
```bash
python mig.py
```

### Creating an Admin User

You need at least one admin user to access the admin functionalities. Use the `create_admin.py` script to create one:

```bash
python create_admin.py
```
Follow the prompts to enter a username and password.

### Running the Application

To start the FastAPI server:

```bash
uvicorn main:app --reload
```
The API will be accessible at `http://127.0.0.1:8000`. The interactive API documentation (Swagger UI) will be available at `http://127.0.0.1:8000/docs`.

## API Endpoints

### Seller Endpoints

-   `POST /seller/submit`: Submit a new gadget listing.

### Buyer Endpoints

-   `POST /buyer/request`: Submit a request for a specific gadget.
-   `POST /buyer/question`: Submit a question about a listing.

### Admin Endpoints

-   `POST /admin/login`: Authenticate as an administrator and receive an access token.
-   `POST /admin/add`: Add a new gadget listing (requires admin authentication).
-   `GET /admin/dashboard`: Retrieve comprehensive dashboard data (pending, active, sold listings, buyer questions, gadget requests).
-   `PUT /admin/listings/{listing_id}`: Update details of a specific listing.
-   `PATCH /admin/listings/{listing_id}/status`: Update the status of a listing (e.g., `AVAILABLE`, `SOLD`, `DELETED`).
-   `POST /admin/settings`: Update admin settings, such as the WhatsApp contact number.
-   `DELETE /admin/questions/{question_id}`: Delete a buyer question.
-   `GET /admin/listings/pending`: Get all pending listings.
-   `POST /admin/listings/bulk`: Perform bulk actions on listings (e.g., change status for multiple listings).

### Public Endpoints

-   `GET /listings`: Retrieve a list of available public listings with optional filters (gadget type, price range, condition).
-   `GET /listings/approved`: Retrieve a list of approved listings.
-   `GET /uploads/{filename}`: Serve uploaded image files.

## Authentication

Admin endpoints are protected by JWT (JSON Web Token) authentication. To access these endpoints, you must first obtain an access token by logging in via `/admin/login`. Include this token in the `Authorization` header of subsequent requests as a Bearer token.

Example: `Authorization: Bearer YOUR_ACCESS_TOKEN`

## Project Structure

```
.
├── main.py                 # Main FastAPI application
├── create_admin.py         # Script to create an admin user
├── mig.py                  # Database migration script
├── requirements.txt        # Python dependencies
├── reselling.db            # SQLite database file (generated)
├── __pycache__/            # Python cache directory
└── uploads/                # Directory for uploaded gadget photos
```

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## License

This project is open-source and available under the [MIT License](LICENSE).

## Contact

For any questions or inquiries, please reach out to me on GitHub: [aqdev-tech](https://github.com/aqdev-tech)
