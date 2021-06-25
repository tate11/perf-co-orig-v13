.. image:: https://img.shields.io/badge/licence-OPL--1-blue.svg
    :alt: License: OPL-1
.. image:: https://img.shields.io/badge/Odoo-13.0-a24689.svg
    :alt: Odoo Version: 13.0

#################
Return Merchandise authorization (RMA)
#################

Description
-----------
Return Merchandise authorization (RMA) management.

Features
--------

- This module helps create and manage RMA orders from Sales/Purchase orders.
- Manage Return/Delivery orders and Refunds for each RMA type.


Usage
-----

#. Either install this module to your database.
#. Create RMA orders from a Purchase/Sales orders (PO/SO).
#. Particular workflow for each RMA case based on RMA type (Return/Exchange):

- SO return: Return -> Refund
- SO exchange: Return -> Delivery
- PO return: Delivery -> Refund
- PO exchange: Delivery -> Receipt.



Commit Version:
---------------

Community: (Dec 07, 2020)

Authors and maintainers:
------------------------
Novobi

Bugs and issues:
----------------
