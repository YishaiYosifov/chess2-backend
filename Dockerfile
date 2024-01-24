FROM python:3.11.7

WORKDIR /workspaces/chess2-backend

COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--reload"]