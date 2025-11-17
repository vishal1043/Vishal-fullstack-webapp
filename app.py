import os
import pymysql

from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from models import db, Project, Client, Contact, Subscriber

pymysql.install_as_MySQLdb()
load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "devkey")

    # First try full URL from .env
    db_url = os.getenv("DATABASE_URL")

   
    if not db_url:
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "3306")
        db_name = os.getenv("DB_NAME", "flipr_app")

        if db_password:
            db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            db_url = f"mysql+pymysql://{db_user}@{db_host}:{db_port}/{db_name}"

    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    print("Using DB URL:", app.config["SQLALCHEMY_DATABASE_URI"])

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # ----------------- PUBLIC ROUTES -----------------

    @app.route("/")
    def index():
        projects = Project.query.order_by(Project.created_at.desc()).all()
        clients = Client.query.order_by(Client.created_at.desc()).all()
        return render_template("index.html", projects=projects, clients=clients)

    @app.post("/contact")
    def submit_contact():
        full_name = request.form.get("fullName")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        city = request.form.get("city")

        if not (full_name and email and mobile and city):
            flash("Please fill all fields in the contact form.", "danger")
            return redirect(url_for("index"))

        contact = Contact(
            full_name=full_name,
            email=email,
            mobile=mobile,
            city=city
        )
        db.session.add(contact)
        db.session.commit()
        flash("Thank you! Your contact details have been submitted.", "success")
        return redirect(url_for("index"))

    @app.post("/subscribe")
    def subscribe():
        email = request.form.get("email")

        if not email:
            flash("Please enter an email address.", "danger")
            return redirect(url_for("index"))

        existing = Subscriber.query.filter_by(email=email).first()
        if not existing:
            sub = Subscriber(email=email)
            db.session.add(sub)
            db.session.commit()
            flash("Subscribed successfully to our newsletter!", "success")
        else:
            flash("You are already subscribed!", "info")

        return redirect(url_for("index"))

    # ----------------- ADMIN DASHBOARD -----------------

    @app.route("/admin")
    def admin_panel():
        projects = Project.query.order_by(Project.created_at.desc()).all()
        clients = Client.query.order_by(Client.created_at.desc()).all()
        contacts = Contact.query.order_by(Contact.created_at.desc()).all()
        subscribers = Subscriber.query.order_by(Subscriber.created_at.desc()).all()
        return render_template(
            "admin.html",
            projects=projects,
            clients=clients,
            contacts=contacts,
            subscribers=subscribers
        )

    # -------- PROJECTS CRUD --------

    @app.post("/admin/projects")
    def add_project():
        image_url = request.form.get("image_url")
        name = request.form.get("name")
        description = request.form.get("description")

        if not (image_url and name and description):
            flash("All project fields are required.", "danger")
            return redirect(url_for("admin_panel"))

        project = Project(image_url=image_url, name=name, description=description)
        db.session.add(project)
        db.session.commit()
        flash("Project added successfully!", "success")
        return redirect(url_for("admin_panel"))

    @app.route("/admin/projects/<int:project_id>/edit", methods=["GET", "POST"])
    def edit_project(project_id):
        project = Project.query.get_or_404(project_id)

        if request.method == "POST":
            project.image_url = request.form.get("image_url")
            project.name = request.form.get("name")
            project.description = request.form.get("description")

            if not (project.image_url and project.name and project.description):
                flash("All project fields are required.", "danger")
                return redirect(url_for("edit_project", project_id=project_id))

            db.session.commit()
            flash("Project updated successfully!", "success")
            return redirect(url_for("admin_panel"))

        return render_template("edit_project.html", project=project)

    @app.post("/admin/projects/<int:project_id>/delete")
    def delete_project(project_id):
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        flash("Project deleted.", "success")
        return redirect(url_for("admin_panel"))

    # -------- CLIENTS CRUD --------

    @app.post("/admin/clients")
    def add_client():
        image_url = request.form.get("image_url")
        name = request.form.get("name")
        description = request.form.get("description")
        designation = request.form.get("designation")

        if not (image_url and name and description and designation):
            flash("All client fields are required.", "danger")
            return redirect(url_for("admin_panel"))

        client = Client(
            image_url=image_url,
            name=name,
            description=description,
            designation=designation
        )
        db.session.add(client)
        db.session.commit()
        flash("Client added successfully!", "success")
        return redirect(url_for("admin_panel"))

    @app.route("/admin/clients/<int:client_id>/edit", methods=["GET", "POST"])
    def edit_client(client_id):
        client = Client.query.get_or_404(client_id)

        if request.method == "POST":
            client.image_url = request.form.get("image_url")
            client.name = request.form.get("name")
            client.description = request.form.get("description")
            client.designation = request.form.get("designation")

            if not (client.image_url and client.name and client.description and client.designation):
                flash("All client fields are required.", "danger")
                return redirect(url_for("edit_client", client_id=client_id))

            db.session.commit()
            flash("Client updated successfully!", "success")
            return redirect(url_for("admin_panel"))

        return render_template("edit_client.html", client=client)

    @app.post("/admin/clients/<int:client_id>/delete")
    def delete_client(client_id):
        client = Client.query.get_or_404(client_id)
        db.session.delete(client)
        db.session.commit()
        flash("Client deleted.", "success")
        return redirect(url_for("admin_panel"))

    # -------- CONTACTS CRUD (Edit & Delete) --------

    @app.route("/admin/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
    def edit_contact(contact_id):
        contact = Contact.query.get_or_404(contact_id)

        if request.method == "POST":
            contact.full_name = request.form.get("full_name")
            contact.email = request.form.get("email")
            contact.mobile = request.form.get("mobile")
            contact.city = request.form.get("city")

            if not (contact.full_name and contact.email and contact.mobile and contact.city):
                flash("All contact fields are required.", "danger")
                return redirect(url_for("edit_contact", contact_id=contact_id))

            db.session.commit()
            flash("Contact updated successfully!", "success")
            return redirect(url_for("admin_panel"))

        return render_template("edit_contact.html", contact=contact)

    @app.post("/admin/contacts/<int:contact_id>/delete")
    def delete_contact(contact_id):
        contact = Contact.query.get_or_404(contact_id)
        db.session.delete(contact)
        db.session.commit()
        flash("Contact deleted.", "success")
        return redirect(url_for("admin_panel"))

    # -------- SUBSCRIBERS CRUD (Edit & Delete) --------

    @app.route("/admin/subscribers/<int:subscriber_id>/edit", methods=["GET", "POST"])
    def edit_subscriber(subscriber_id):
        subscriber = Subscriber.query.get_or_404(subscriber_id)

        if request.method == "POST":
            subscriber.email = request.form.get("email")
            if not subscriber.email:
                flash("Email is required.", "danger")
                return redirect(url_for("edit_subscriber", subscriber_id=subscriber_id))

            db.session.commit()
            flash("Subscriber updated successfully!", "success")
            return redirect(url_for("admin_panel"))

        return render_template("edit_subscriber.html", subscriber=subscriber)

    @app.post("/admin/subscribers/<int:subscriber_id>/delete")
    def delete_subscriber(subscriber_id):
        subscriber = Subscriber.query.get_or_404(subscriber_id)
        db.session.delete(subscriber)
        db.session.commit()
        flash("Subscriber deleted.", "success")
        return redirect(url_for("admin_panel"))

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT env var
    app.run(host="0.0.0.0", port=port, debug=False)

