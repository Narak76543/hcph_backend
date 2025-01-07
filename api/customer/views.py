from .models import Customer
from db import db
from main import app
from .schemas import CustomerModel

@app.post("/customer", tags=["customer"])
async def get_customer():
    customer = db.query(Customer). \
        filter(Customer.id == '00000208'). \
        first()
        
    if customer:
        return Customer
        
    return {"error": "Customer not found"}

@app.post("/customer/create", tags=["customer"])
async def create_customer(
    customer: CustomerModel
):
    new_customer = Customer(
        first_name=customer.first_name,
        last_name=customer.last_name
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    
    return {
        "id": new_customer.id,
        "first_name": new_customer.first_name,
        "last_name": new_customer.last_name
    }
    
@app.delete("/customer/{customer_id}", tags=["customer"])
async def delete_customer(
    customer_id: str
):
    customer = db.query(Customer). \
        filter(Customer.id == customer_id). \
        first()
    
    if customer:
        db.delete(customer)
        db.commit()
        return {"message": "Customer deleted successfully"}
    
    return {"error": "Customer not found"}

@app.put("/customer/{customer_id}", tags=["customer"])
async def update_customer(
    customer_id: str, 
    customer: CustomerModel
):
    existing_customer = db.query(Customer). \
        filter(Customer.id == customer_id). \
        first()
    
    if existing_customer:
        existing_customer.first_name = customer.first_name
        existing_customer.last_name = customer.last_name
        db.commit()
        db.refresh(existing_customer)
        return {
            "id": existing_customer.id,
            "first_name": existing_customer.first_name,
            "last_name": existing_customer.last_name
        }
    
    return {"error": "Customer not found"}