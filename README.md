# WMS Core Engine

The software core of a Warehouse Management System (WMS) built with Python.

This project implements the core business logic for product management, inventory management, order management, stock reservation, payment, shipping, stock transfers, returns, quality control, and refunds using a layered architecture.

The goal of the project is to provide a UI-independent core that can later be connected to a Web UI, API, or other user interfaces.

---

## Main Features

- Product management
- Support for different Product types
- Warehouse and inventory management
- Batch management
- Inventory reservation
- Inventory allocation using FIFO / LIFO / FEFO
- Order management
- Pricing and discount calculation
- Sales rules
- Order state management
- Payment processing
- Order shipping
- Order delivery
- Stock transfers between warehouses
- Return management
- Quality control for returned products
- Moving returned products to sellable inventory or quarantine
- Refund processing
- Inventory and financial transaction recording
- JSON data persistence and recovery
- Unit and Integration tests
- Complete system scenario execution through `main.py`

---

# Architecture

The project is designed around separation of concerns.

The overall system flow is:

````text
Product / Catalog
       |
       v
Inventory
       |
       v
Order
       |
       v
Sales Rules
       |
       v
Pricing
       |
       v
Reservation
       |
       v
Payment
       |
       v
Shipment
       |
       v
Delivery
       |
       v
Return Request
       |
       v
Receiving
       |
       v
Quality Control
       |
       v
RMA
       |
       +----> Sellable Inventory
       |
       +----> Quarantine
       |
       v
Refund


## Order Cancellation Policy

Order cancellation is supported before shipment.

- CREATED orders can be cancelled directly.
- RESERVED orders are cancelled by releasing all active reservations.
- PAID orders can also be cancelled before shipment; their inventory reservations are released.
- A payment transaction remains recorded as a financial/audit record and is not automatically deleted when an order is cancelled.
- Refunds are handled separately through the return/refund flow.
- SHIPPED and DELIVERED orders cannot be cancelled through the normal cancellation operation and must use the RMA/return process.

## Technologies

- Python
- pytest

## Installation

Install the project dependencies:

```bash
pip install -r requirements.txt
````
