# WMS Core Engine

A Python-based Warehouse Management System core engine designed using Object-Oriented Programming and Clean Architecture principles.

The project models the main warehouse and logistics lifecycle, including product catalog management, inventory operations, order processing, stock allocation, shipment, warehouse transfers, reverse logistics, returns, refunds, and JSON persistence.

## Project Overview

WMS Core Engine is a backend/domain-oriented warehouse management system developed without using web frameworks or external databases.

The main goal of the project is not only to create Python classes, but to design a maintainable domain structure where:

- Business logic is separated from persistence.
- Domain rules are implemented in appropriate models and services.
- Order and return lifecycles are controlled through state machines.
- Inventory allocation strategies are replaceable.
- Pricing and business rules can be extended independently.
- Objects can be serialized to and restored from JSON.
- Business behavior is covered by unit and integration tests.

## Main Features

### Product Catalog

The catalog supports different product types:

- BaseProduct
- VariantProduct
- BundleProduct
- PerishableProduct
- SerializedProduct

Product validation includes fields such as:

- SKU
- Name
- Barcode
- Category
- Base price

### Inventory Management

The inventory module supports:

- Multiple warehouses
- Stock batches
- Inventory quantities
- Stock reservations
- Stock receiving
- Inventory ledger
- Inventory transactions
- Warehouse transfers
- Quarantine inventory

### Stock Allocation

The system supports replaceable allocation strategies such as:

- FIFO
- LIFO
- FEFO

These strategies allow inventory allocation behavior to be changed without changing the main order processing logic.

### Order Management

Orders support a controlled lifecycle including:

- Order creation
- Adding order items
- Pricing
- Sales rules
- Stock reservation
- Payment
- Shipment
- Delivery
- Order state transitions

### Pricing and Business Rules

The pricing system supports:

- Product pricing
- Price calculation
- Pricing strategies
- Sales rules
- Prerequisite rules
- Business validation

Business rules are kept outside repositories so that persistence classes remain responsible only for storing and retrieving data.

### Warehouse Transfer

The system supports transferring inventory between warehouses.

The transfer lifecycle includes:

- Source warehouse
- Destination warehouse
- Transfer creation
- Transit state
- Destination receiving
- Inventory updates
- Transfer ledger records

### Reverse Logistics

The reverse logistics flow supports:

- Return requests
- Return eligibility
- Return receiving
- Quality control
- RMA processing
- Sellable inventory
- Quarantine inventory
- Refund processing

Return requests use a state machine to control valid state transitions.

### JSON Persistence

The project provides serialization and deserialization functionality for domain objects.

The persistence layer can store and restore application state using JSON without using:

- SQL databases
- SQLite
- ORM
- External storage services

The snapshot mechanism is designed to preserve the state of the system so that objects can be loaded again after application restart.

### Testing

The project contains both unit and integration tests.

Tests focus on:

- Domain behavior
- Business rules
- Boundary cases
- Invalid inputs
- State transitions
- Inventory behavior
- Pricing
- Orders
- Returns
- JSON serialization/deserialization
- Snapshot round trips
- Integration between major services

## Architecture

The project follows a layered architecture.

```text
                 WMS Core Engine
                       |
        +--------------+--------------+
        |              |              |
      Domain        Services      Repositories
        |              |              |
   Models/Enums    Business Logic   Persistence
   Exceptions      Validation       JSON
   State Machines  Rules/Strategy
        |
        +-----------------------------+
                                      |
                                  Serialization
                                  Deserialization