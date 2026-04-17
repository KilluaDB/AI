"""
E-Commerce Domain Configuration

Ground-truth configuration for e-commerce database schema design including:
- PostgreSQL type mappings for common e-commerce attributes
- Cardinality rules with SQL implementations
- Lookup tables for standard values
- Entity type definitions
- Common relationship patterns
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EcommercePlatformType(Enum):
    """Types of e-commerce platforms"""
    B2C = "b2c"  # Business to Consumer
    B2B = "b2b"  # Business to Business
    C2C = "c2c"  # Consumer to Consumer (marketplace)
    MARKETPLACE = "marketplace"
    SUBSCRIPTION = "subscription"


@dataclass
class EcommerceConfig:
    """Configuration for e-commerce domain"""
    platform_type: EcommercePlatformType = EcommercePlatformType.B2C
    multi_currency: bool = True
    multi_language: bool = False
    tax_enabled: bool = True
    inventory_tracking: bool = True
    
    # Additional options
    options: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PostgreSQL Type Mappings for E-Commerce Attributes
# ============================================================================

ECOMMERCE_POSTGRES_TYPE_MAP: Dict[str, str] = {
    # Primary Keys
    "id": "UUID PRIMARY KEY DEFAULT gen_random_uuid()",
    "customer_id": "UUID NOT NULL",
    "product_id": "UUID NOT NULL",
    "order_id": "UUID NOT NULL",
    "cart_id": "UUID NOT NULL",
    "category_id": "UUID NOT NULL",
    "review_id": "UUID NOT NULL",
    "payment_id": "UUID NOT NULL",
    "shipment_id": "UUID NOT NULL",
    "address_id": "UUID NOT NULL",
    "coupon_id": "UUID NOT NULL",
    "wishlist_id": "UUID NOT NULL",
    "vendor_id": "UUID NOT NULL",
    "warehouse_id": "UUID NOT NULL",
    "inventory_id": "UUID NOT NULL",
    
    # Customer Information
    "email": "VARCHAR(255) NOT NULL UNIQUE",
    "password_hash": "VARCHAR(255) NOT NULL",
    "first_name": "VARCHAR(100)",
    "last_name": "VARCHAR(100)",
    "full_name": "VARCHAR(255)",
    "phone": "VARCHAR(20)",
    "phone_number": "VARCHAR(20)",
    "mobile": "VARCHAR(20)",
    "date_of_birth": "DATE",
    "gender": "VARCHAR(20)",
    "customer_type": "VARCHAR(50) DEFAULT 'regular'",
    "loyalty_points": "INTEGER DEFAULT 0",
    "loyalty_tier": "VARCHAR(50) DEFAULT 'bronze'",
    
    # Product Information
    "sku": "VARCHAR(100) NOT NULL UNIQUE",
    "product_name": "VARCHAR(255) NOT NULL",
    "product_title": "VARCHAR(255) NOT NULL",
    "slug": "VARCHAR(255) UNIQUE",
    "description": "TEXT",
    "short_description": "VARCHAR(500)",
    "long_description": "TEXT",
    "brand": "VARCHAR(100)",
    "brand_name": "VARCHAR(100)",
    "manufacturer": "VARCHAR(255)",
    "model": "VARCHAR(100)",
    "upc": "VARCHAR(20)",
    "ean": "VARCHAR(20)",
    "isbn": "VARCHAR(20)",
    "mpn": "VARCHAR(100)",
    "weight": "DECIMAL(10,3)",
    "weight_unit": "VARCHAR(10) DEFAULT 'kg'",
    "length": "DECIMAL(10,2)",
    "width": "DECIMAL(10,2)",
    "height": "DECIMAL(10,2)",
    "dimension_unit": "VARCHAR(10) DEFAULT 'cm'",
    "color": "VARCHAR(50)",
    "size": "VARCHAR(50)",
    "material": "VARCHAR(100)",
    "product_type": "VARCHAR(50)",
    "is_digital": "BOOLEAN DEFAULT FALSE",
    "is_downloadable": "BOOLEAN DEFAULT FALSE",
    "download_url": "VARCHAR(2048)",
    "download_limit": "INTEGER",
    "download_expiry_days": "INTEGER",
    
    # Pricing
    "price": "DECIMAL(12,2) NOT NULL",
    "unit_price": "DECIMAL(12,2) NOT NULL",
    "cost_price": "DECIMAL(12,2)",
    "sale_price": "DECIMAL(12,2)",
    "compare_at_price": "DECIMAL(12,2)",
    "regular_price": "DECIMAL(12,2)",
    "discount_price": "DECIMAL(12,2)",
    "wholesale_price": "DECIMAL(12,2)",
    "msrp": "DECIMAL(12,2)",
    "currency": "CHAR(3) DEFAULT 'USD'",
    "currency_code": "CHAR(3) DEFAULT 'USD'",
    "tax_rate": "DECIMAL(5,4)",
    "tax_amount": "DECIMAL(12,2)",
    "tax_class": "VARCHAR(50)",
    "is_taxable": "BOOLEAN DEFAULT TRUE",
    
    # Inventory
    "quantity": "INTEGER NOT NULL DEFAULT 0",
    "stock_quantity": "INTEGER NOT NULL DEFAULT 0",
    "reserved_quantity": "INTEGER DEFAULT 0",
    "available_quantity": "INTEGER GENERATED ALWAYS AS (stock_quantity - reserved_quantity) STORED",
    "min_stock_level": "INTEGER DEFAULT 0",
    "max_stock_level": "INTEGER",
    "reorder_point": "INTEGER",
    "reorder_quantity": "INTEGER",
    "stock_status": "VARCHAR(50) DEFAULT 'in_stock'",
    "backorder_allowed": "BOOLEAN DEFAULT FALSE",
    "track_inventory": "BOOLEAN DEFAULT TRUE",
    "inventory_policy": "VARCHAR(50) DEFAULT 'deny'",
    
    # Order Information
    "order_number": "VARCHAR(50) NOT NULL UNIQUE",
    "order_status": "VARCHAR(50) NOT NULL DEFAULT 'pending'",
    "payment_status": "VARCHAR(50) NOT NULL DEFAULT 'pending'",
    "fulfillment_status": "VARCHAR(50) DEFAULT 'unfulfilled'",
    "order_date": "TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()",
    "shipped_date": "TIMESTAMP WITH TIME ZONE",
    "delivered_date": "TIMESTAMP WITH TIME ZONE",
    "cancelled_date": "TIMESTAMP WITH TIME ZONE",
    "subtotal": "DECIMAL(12,2) NOT NULL",
    "shipping_cost": "DECIMAL(12,2) DEFAULT 0",
    "discount_amount": "DECIMAL(12,2) DEFAULT 0",
    "total_amount": "DECIMAL(12,2) NOT NULL",
    "grand_total": "DECIMAL(12,2) NOT NULL",
    "line_total": "DECIMAL(12,2) NOT NULL",
    "notes": "TEXT",
    "order_notes": "TEXT",
    "internal_notes": "TEXT",
    "gift_message": "TEXT",
    "is_gift": "BOOLEAN DEFAULT FALSE",
    
    # Cart
    "cart_token": "VARCHAR(255) UNIQUE",
    "session_id": "VARCHAR(255)",
    "cart_status": "VARCHAR(50) DEFAULT 'active'",
    "expires_at": "TIMESTAMP WITH TIME ZONE",
    "abandoned_at": "TIMESTAMP WITH TIME ZONE",
    
    # Payment
    "payment_method": "VARCHAR(50) NOT NULL",
    "payment_gateway": "VARCHAR(100)",
    "transaction_id": "VARCHAR(255)",
    "authorization_code": "VARCHAR(100)",
    "card_last_four": "CHAR(4)",
    "card_brand": "VARCHAR(50)",
    "card_exp_month": "SMALLINT",
    "card_exp_year": "SMALLINT",
    "billing_address_id": "UUID",
    "payment_date": "TIMESTAMP WITH TIME ZONE",
    "refund_amount": "DECIMAL(12,2)",
    "refund_reason": "TEXT",
    "refund_date": "TIMESTAMP WITH TIME ZONE",
    
    # Shipping
    "shipping_method": "VARCHAR(100)",
    "shipping_carrier": "VARCHAR(100)",
    "tracking_number": "VARCHAR(255)",
    "tracking_url": "VARCHAR(2048)",
    "shipping_address_id": "UUID",
    "estimated_delivery": "DATE",
    "actual_delivery": "DATE",
    "shipping_label_url": "VARCHAR(2048)",
    "shipping_weight": "DECIMAL(10,3)",
    "package_count": "INTEGER DEFAULT 1",
    
    # Address
    "address_type": "VARCHAR(50) DEFAULT 'shipping'",
    "address_line1": "VARCHAR(255) NOT NULL",
    "address_line2": "VARCHAR(255)",
    "street": "VARCHAR(255)",
    "city": "VARCHAR(100) NOT NULL",
    "state": "VARCHAR(100)",
    "province": "VARCHAR(100)",
    "region": "VARCHAR(100)",
    "postal_code": "VARCHAR(20)",
    "zip_code": "VARCHAR(20)",
    "country": "VARCHAR(100) NOT NULL",
    "country_code": "CHAR(2)",
    "is_default": "BOOLEAN DEFAULT FALSE",
    "is_billing": "BOOLEAN DEFAULT FALSE",
    "is_shipping": "BOOLEAN DEFAULT TRUE",
    
    # Category
    "category_name": "VARCHAR(255) NOT NULL",
    "category_slug": "VARCHAR(255) UNIQUE",
    "parent_category_id": "UUID",
    "category_level": "SMALLINT DEFAULT 0",
    "category_path": "VARCHAR(1000)",
    "display_order": "INTEGER DEFAULT 0",
    "sort_order": "INTEGER DEFAULT 0",
    
    # Review & Rating
    "rating": "SMALLINT CHECK (rating >= 1 AND rating <= 5)",
    "review_title": "VARCHAR(255)",
    "review_text": "TEXT",
    "review_status": "VARCHAR(50) DEFAULT 'pending'",
    "is_verified_purchase": "BOOLEAN DEFAULT FALSE",
    "helpful_votes": "INTEGER DEFAULT 0",
    "reported_count": "INTEGER DEFAULT 0",
    
    # Coupon & Discount
    "coupon_code": "VARCHAR(50) NOT NULL UNIQUE",
    "discount_type": "VARCHAR(50) NOT NULL",
    "discount_value": "DECIMAL(12,2) NOT NULL",
    "discount_percentage": "DECIMAL(5,2)",
    "min_purchase_amount": "DECIMAL(12,2)",
    "max_discount_amount": "DECIMAL(12,2)",
    "usage_limit": "INTEGER",
    "usage_count": "INTEGER DEFAULT 0",
    "usage_limit_per_customer": "INTEGER DEFAULT 1",
    "valid_from": "TIMESTAMP WITH TIME ZONE",
    "valid_until": "TIMESTAMP WITH TIME ZONE",
    "is_active": "BOOLEAN DEFAULT TRUE",
    
    # Vendor/Seller
    "vendor_name": "VARCHAR(255) NOT NULL",
    "store_name": "VARCHAR(255)",
    "commission_rate": "DECIMAL(5,4)",
    "payout_method": "VARCHAR(50)",
    "bank_account": "VARCHAR(50)",
    "tax_id": "VARCHAR(50)",
    "verification_status": "VARCHAR(50) DEFAULT 'pending'",
    
    # Warehouse/Location
    "warehouse_name": "VARCHAR(255) NOT NULL",
    "warehouse_code": "VARCHAR(50) UNIQUE",
    "location_name": "VARCHAR(255)",
    "bin_location": "VARCHAR(100)",
    "aisle": "VARCHAR(50)",
    "shelf": "VARCHAR(50)",
    "capacity": "INTEGER",
    
    # Image & Media
    "image_url": "VARCHAR(2048)",
    "thumbnail_url": "VARCHAR(2048)",
    "gallery_images": "JSONB",
    "video_url": "VARCHAR(2048)",
    "alt_text": "VARCHAR(255)",
    "media_type": "VARCHAR(50)",
    
    # SEO
    "meta_title": "VARCHAR(255)",
    "meta_description": "TEXT",
    "meta_keywords": "TEXT",
    "canonical_url": "VARCHAR(2048)",
    
    # Timestamps
    "created_at": "TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()",
    "updated_at": "TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()",
    "deleted_at": "TIMESTAMP WITH TIME ZONE",
    "published_at": "TIMESTAMP WITH TIME ZONE",
    "last_login_at": "TIMESTAMP WITH TIME ZONE",
    "last_order_at": "TIMESTAMP WITH TIME ZONE",
    
    # Status & Flags
    "status": "VARCHAR(50) DEFAULT 'active'",
    "is_enabled": "BOOLEAN DEFAULT TRUE",
    "is_visible": "BOOLEAN DEFAULT TRUE",
    "is_featured": "BOOLEAN DEFAULT FALSE",
    "is_bestseller": "BOOLEAN DEFAULT FALSE",
    "is_new_arrival": "BOOLEAN DEFAULT FALSE",
    "is_on_sale": "BOOLEAN DEFAULT FALSE",
    "is_verified": "BOOLEAN DEFAULT FALSE",
    "requires_shipping": "BOOLEAN DEFAULT TRUE",
    
    # Metadata
    "metadata": "JSONB",
    "attributes": "JSONB",
    "custom_fields": "JSONB",
    "tags": "TEXT[]",
    "options": "JSONB",
    "variants": "JSONB",
}


# ============================================================================
# Cardinality Mappings with SQL Implementations
# ============================================================================

ECOMMERCE_CARDINALITY_MAP: Dict[str, Dict[str, Any]] = {
    "0..1": {
        "nullable": True,
        "constraint": None,
        "description": "Optional single reference (e.g., product may have sale_price)",
        "sql_example": "sale_price DECIMAL(12,2) -- nullable, optional discount price"
    },
    "1..1": {
        "nullable": False,
        "constraint": "NOT NULL",
        "description": "Required single reference (e.g., order must have customer)",
        "sql_example": "customer_id UUID NOT NULL REFERENCES customer(id)"
    },
    "0..*": {
        "nullable": True,
        "constraint": None,
        "description": "Optional multiple (e.g., product may have many reviews)",
        "requires_junction_table": False,
        "sql_example": """
-- product_review table with optional relationship
CREATE TABLE product_review (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES product(id),
    customer_id UUID REFERENCES customer(id),  -- nullable for anonymous
    rating SMALLINT NOT NULL,
    review_text TEXT
);"""
    },
    "1..*": {
        "nullable": False,
        "constraint": "NOT NULL",
        "description": "Required multiple (e.g., order must have at least one item)",
        "requires_junction_table": False,
        "sql_example": """
-- order_item ensures at least one item per order
CREATE TABLE order_item (
    id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(id),
    product_id UUID NOT NULL REFERENCES product(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12,2) NOT NULL
);
-- Application logic must ensure at least one item per order"""
    },
    "N:1": {
        "description": "Many-to-one (e.g., many products belong to one category)",
        "sql_example": """
-- product.category_id references category
ALTER TABLE product 
ADD COLUMN category_id UUID REFERENCES category(id);"""
    },
    "1:N": {
        "description": "One-to-many (e.g., customer has many orders)",
        "sql_example": """
-- orders.customer_id references customer
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    customer_id UUID NOT NULL REFERENCES customer(id),
    order_date TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);"""
    },
    "M:N": {
        "description": "Many-to-many (e.g., products and tags)",
        "requires_junction_table": True,
        "sql_example": """
-- Junction table for product <-> tag relationship
CREATE TABLE product_tag (
    product_id UUID NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tag(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, tag_id)
);"""
    },
}


# ============================================================================
# Lookup Tables for Standard Values
# ============================================================================

ECOMMERCE_LOOKUP_TABLES: Dict[str, List[str]] = {
    "order_status": [
        "pending", "confirmed", "processing", "shipped", 
        "delivered", "completed", "cancelled", "refunded",
        "on_hold", "failed", "returned"
    ],
    "payment_status": [
        "pending", "authorized", "paid", "partially_paid",
        "refunded", "partially_refunded", "failed", "cancelled", "voided"
    ],
    "fulfillment_status": [
        "unfulfilled", "partial", "fulfilled", "restocked"
    ],
    "stock_status": [
        "in_stock", "out_of_stock", "backorder", "preorder", "discontinued"
    ],
    "payment_method": [
        "credit_card", "debit_card", "paypal", "stripe", "apple_pay",
        "google_pay", "bank_transfer", "cash_on_delivery", "cryptocurrency",
        "buy_now_pay_later", "gift_card", "store_credit"
    ],
    "shipping_carrier": [
        "fedex", "ups", "usps", "dhl", "aramex", "dpd", 
        "royal_mail", "australia_post", "canada_post", "other"
    ],
    "discount_type": [
        "percentage", "fixed_amount", "free_shipping", 
        "buy_x_get_y", "tiered", "bundle"
    ],
    "address_type": [
        "shipping", "billing", "both"
    ],
    "customer_type": [
        "regular", "wholesale", "vip", "guest", "business"
    ],
    "loyalty_tier": [
        "bronze", "silver", "gold", "platinum", "diamond"
    ],
    "review_status": [
        "pending", "approved", "rejected", "flagged"
    ],
    "product_type": [
        "simple", "variable", "grouped", "bundle", "virtual", "downloadable"
    ],
    "currency_code": [
        "USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY", "INR", "BRL", "MXN"
    ],
    "weight_unit": [
        "kg", "g", "lb", "oz"
    ],
    "dimension_unit": [
        "cm", "m", "in", "ft"
    ],
}


# ============================================================================
# Common E-Commerce Entities
# ============================================================================

ECOMMERCE_ENTITY_TYPES: List[str] = [
    "Customer",
    "Product",
    "Category",
    "Order",
    "OrderItem",
    "Cart",
    "CartItem",
    "Payment",
    "Shipment",
    "Address",
    "Review",
    "Wishlist",
    "Coupon",
    "Discount",
    "Vendor",
    "Warehouse",
    "Inventory",
    "Tag",
    "Attribute",
    "ProductVariant",
    "ProductImage",
]


# ============================================================================
# Common E-Commerce Relationships
# ============================================================================

ECOMMERCE_RELATIONSHIPS: Dict[str, Dict[str, Any]] = {
    "customer_order": {
        "from": "Customer",
        "to": "Order",
        "cardinality": "1:N",
        "description": "One customer can have many orders"
    },
    "order_orderitem": {
        "from": "Order",
        "to": "OrderItem",
        "cardinality": "1:N",
        "description": "One order contains many order items"
    },
    "product_orderitem": {
        "from": "Product",
        "to": "OrderItem",
        "cardinality": "1:N",
        "description": "One product can be in many order items"
    },
    "category_product": {
        "from": "Category",
        "to": "Product",
        "cardinality": "1:N",
        "description": "One category contains many products"
    },
    "product_category": {
        "from": "Product",
        "to": "Category",
        "cardinality": "M:N",
        "description": "Products can belong to multiple categories"
    },
    "customer_cart": {
        "from": "Customer",
        "to": "Cart",
        "cardinality": "1:1",
        "description": "One customer has one active cart"
    },
    "cart_cartitem": {
        "from": "Cart",
        "to": "CartItem",
        "cardinality": "1:N",
        "description": "One cart contains many cart items"
    },
    "product_review": {
        "from": "Product",
        "to": "Review",
        "cardinality": "1:N",
        "description": "One product can have many reviews"
    },
    "customer_review": {
        "from": "Customer",
        "to": "Review",
        "cardinality": "1:N",
        "description": "One customer can write many reviews"
    },
    "order_payment": {
        "from": "Order",
        "to": "Payment",
        "cardinality": "1:N",
        "description": "One order can have multiple payments"
    },
    "order_shipment": {
        "from": "Order",
        "to": "Shipment",
        "cardinality": "1:N",
        "description": "One order can have multiple shipments"
    },
    "customer_address": {
        "from": "Customer",
        "to": "Address",
        "cardinality": "1:N",
        "description": "One customer can have multiple addresses"
    },
    "product_inventory": {
        "from": "Product",
        "to": "Inventory",
        "cardinality": "1:N",
        "description": "One product tracked across multiple warehouses"
    },
    "customer_wishlist": {
        "from": "Customer",
        "to": "Wishlist",
        "cardinality": "1:N",
        "description": "One customer can have multiple wishlists"
    },
    "product_tag": {
        "from": "Product",
        "to": "Tag",
        "cardinality": "M:N",
        "description": "Products can have multiple tags and vice versa"
    },
    "product_variant": {
        "from": "Product",
        "to": "ProductVariant",
        "cardinality": "1:N",
        "description": "One product can have multiple variants (size, color)"
    },
    "vendor_product": {
        "from": "Vendor",
        "to": "Product",
        "cardinality": "1:N",
        "description": "One vendor can sell many products (marketplace)"
    },
    "category_subcategory": {
        "from": "Category",
        "to": "Category",
        "cardinality": "1:N",
        "description": "Self-referential for category hierarchy"
    },
}
