from setuptools import setup, find_packages

setup(
    name="user-service",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'flask==3.0.0',
        'flask-sqlalchemy==3.1.1',
        'flask-jwt-extended==4.5.3',
        'flask-limiter==3.5.0',
        'redis==5.0.1',
        'psycopg2-binary==2.9.9',
        'python-dotenv==1.0.0',
        'werkzeug==3.0.1',
        'flask-cors==4.0.0',
    ],
)
