"""
E-Commerce RAG Retriever

Provides ground-truth knowledge for e-commerce database schema design.
This retriever contains comprehensive knowledge about:
- Entity definitions (Customer, Product, Order, etc.)
- Relationship patterns with SQL examples
- PostgreSQL data type mappings
- Cardinality rules
- Normalization rules with e-commerce examples
- Design patterns (shopping cart, inventory, pricing)
- Constraint rules for data validation
"""

from typing import List, Optional
from ...base_rag import BaseRAGRetriever, RAGChunk, RAGConfig, ChunkType, generate_chunk_id


class EcommerceRAGRetriever(BaseRAGRetriever):
    """
    E-Commerce domain RAG retriever with ground-truth knowledge.
    
    Provides comprehensive knowledge for designing e-commerce database schemas
    including entity definitions, relationship patterns, and best practices.
    """
    
    def __init__(self, config: Optional[RAGConfig] = None):
        super().__init__(config)
    
    def get_domain(self) -> str:
        """Return the domain name."""
        return "ecommerce"
    
    def _load_domain_knowledge(self) -> List[RAGChunk]:
        """Load all e-commerce ground-truth knowledge chunks."""
        chunks = []
        
        # Entity definitions
        chunks.extend(self._get_entity_definitions())
        
        # Relationship patterns
        chunks.extend(self._get_relationship_patterns())
        
        # Data type guidelines
        chunks.extend(self._get_datatype_guidelines())
        
        # Cardinality rules
        chunks.extend(self._get_cardinality_rules())
        
        # Normalization rules
        chunks.extend(self._get_normalization_rules())
        
        # E-commerce design patterns
        chunks.extend(self._get_ecommerce_patterns())
        
        # Constraint rules
        chunks.extend(self._get_constraint_rules())
        
        return chunks
    
    def _get_entity_definitions(self) -> List[RAGChunk]:
        """Get entity definition chunks for common e-commerce entities."""
        entities = []
        
        # Customer Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "customer", "definition"),
            content="""
ENTITY: Customer
DESCRIPTION: Represents a registered user or buyer in the e-commerce system.

REQUIRED ATTRIBUTES:
- customer_id: UUID PRIMARY KEY - Unique identifier
- email: VARCHAR(255) NOT NULL UNIQUE - Login and contact email
- password_hash: VARCHAR(255) NOT NULL - Hashed password for authentication
- created_at: TIMESTAMP WITH TIME ZONE - Registration timestamp

RECOMMENDED ATTRIBUTES:
- first_name: VARCHAR(100) - Customer first name
- last_name: VARCHAR(100) - Customer last name
- phone: VARCHAR(20) - Contact phone number
- date_of_birth: DATE - For age verification and marketing
- gender: VARCHAR(20) - Optional demographic info
- customer_type: VARCHAR(50) - regular, wholesale, vip, guest
- loyalty_points: INTEGER DEFAULT 0 - Rewards program points
- loyalty_tier: VARCHAR(50) - bronze, silver, gold, platinum
- is_verified: BOOLEAN - Email/phone verification status
- is_active: BOOLEAN - Account active status
- last_login_at: TIMESTAMP - Last login timestamp
- last_order_at: TIMESTAMP - Last order timestamp
- updated_at: TIMESTAMP WITH TIME ZONE - Last update timestamp

RELATIONSHIPS:
- Customer 1:N Order - Customer places many orders
- Customer 1:N Address - Customer has multiple addresses
- Customer 1:1 Cart - Customer has one active cart
- Customer 1:N Review - Customer writes many reviews
- Customer 1:N Wishlist - Customer has multiple wishlists

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_customer_email ON customer(email);
- CREATE INDEX idx_customer_phone ON customer(phone);
- CREATE INDEX idx_customer_created ON customer(created_at);
- CREATE INDEX idx_customer_loyalty ON customer(loyalty_tier);

SPECIAL CONSIDERATIONS:
- Store password_hash, never plain passwords
- Consider GDPR compliance for personal data
- Implement soft delete with is_active flag
- Track consent for marketing communications
""",
            resource_type="Customer",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["customer", "user", "account", "buyer", "member"],
            trust_level=1.0
        ))
        
        # Product Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "product", "definition"),
            content="""
ENTITY: Product
DESCRIPTION: Represents a sellable item in the e-commerce catalog.

REQUIRED ATTRIBUTES:
- product_id: UUID PRIMARY KEY - Unique identifier
- sku: VARCHAR(100) NOT NULL UNIQUE - Stock Keeping Unit
- product_name: VARCHAR(255) NOT NULL - Display name
- price: DECIMAL(12,2) NOT NULL - Current selling price
- created_at: TIMESTAMP WITH TIME ZONE - Creation timestamp

RECOMMENDED ATTRIBUTES:
- slug: VARCHAR(255) UNIQUE - URL-friendly identifier
- description: TEXT - Full product description
- short_description: VARCHAR(500) - Brief description for listings
- brand: VARCHAR(100) - Brand name
- manufacturer: VARCHAR(255) - Manufacturer name
- model: VARCHAR(100) - Model number
- upc: VARCHAR(20) - Universal Product Code
- cost_price: DECIMAL(12,2) - Purchase/manufacturing cost
- sale_price: DECIMAL(12,2) - Discounted price
- compare_at_price: DECIMAL(12,2) - Original price for comparison
- currency: CHAR(3) DEFAULT 'USD' - Currency code
- tax_class: VARCHAR(50) - Tax category
- is_taxable: BOOLEAN DEFAULT TRUE - Tax applicability
- weight: DECIMAL(10,3) - Product weight
- weight_unit: VARCHAR(10) - kg, g, lb, oz
- length, width, height: DECIMAL(10,2) - Dimensions
- stock_quantity: INTEGER DEFAULT 0 - Available inventory
- stock_status: VARCHAR(50) - in_stock, out_of_stock, backorder
- is_visible: BOOLEAN DEFAULT TRUE - Visibility in catalog
- is_featured: BOOLEAN - Featured product flag
- is_digital: BOOLEAN - Digital/downloadable product
- image_url: VARCHAR(2048) - Main product image
- gallery_images: JSONB - Additional images
- meta_title: VARCHAR(255) - SEO title
- meta_description: TEXT - SEO description
- tags: TEXT[] - Product tags array
- attributes: JSONB - Custom attributes
- published_at: TIMESTAMP - Publication date
- updated_at: TIMESTAMP WITH TIME ZONE - Last update

RELATIONSHIPS:
- Product N:1 Category - Product belongs to category
- Product M:N Category - Product in multiple categories (via junction)
- Product 1:N ProductVariant - Product has variants
- Product 1:N ProductImage - Product has multiple images
- Product 1:N Review - Product has reviews
- Product 1:N OrderItem - Product appears in order items
- Product 1:N Inventory - Product tracked in warehouses
- Product M:N Tag - Product has multiple tags

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_product_sku ON product(sku);
- CREATE INDEX idx_product_slug ON product(slug);
- CREATE INDEX idx_product_category ON product(category_id);
- CREATE INDEX idx_product_brand ON product(brand);
- CREATE INDEX idx_product_price ON product(price);
- CREATE INDEX idx_product_status ON product(stock_status);
- CREATE INDEX idx_product_visible ON product(is_visible) WHERE is_visible = TRUE;
- CREATE INDEX idx_product_search ON product USING gin(to_tsvector('english', product_name || ' ' || COALESCE(description, '')));

SPECIAL CONSIDERATIONS:
- Use DECIMAL for prices, never FLOAT
- Implement full-text search for product search
- Consider product versioning for price history
- Handle variants (size, color) via separate table
""",
            resource_type="Product",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["product", "item", "merchandise", "goods", "catalog"],
            trust_level=1.0
        ))
        
        # Category Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "category", "definition"),
            content="""
ENTITY: Category
DESCRIPTION: Hierarchical classification for organizing products.

REQUIRED ATTRIBUTES:
- category_id: UUID PRIMARY KEY - Unique identifier
- category_name: VARCHAR(255) NOT NULL - Display name
- created_at: TIMESTAMP WITH TIME ZONE - Creation timestamp

RECOMMENDED ATTRIBUTES:
- slug: VARCHAR(255) UNIQUE - URL-friendly identifier
- description: TEXT - Category description
- parent_category_id: UUID REFERENCES category(id) - Self-reference for hierarchy
- category_level: SMALLINT DEFAULT 0 - Depth in hierarchy (0=root)
- category_path: VARCHAR(1000) - Materialized path for hierarchy
- display_order: INTEGER DEFAULT 0 - Sort order
- image_url: VARCHAR(2048) - Category image
- is_active: BOOLEAN DEFAULT TRUE - Active status
- is_visible: BOOLEAN DEFAULT TRUE - Visibility in navigation
- meta_title: VARCHAR(255) - SEO title
- meta_description: TEXT - SEO description
- product_count: INTEGER DEFAULT 0 - Cached product count
- updated_at: TIMESTAMP WITH TIME ZONE - Last update

RELATIONSHIPS:
- Category 1:N Product - Category contains products
- Category 1:N Category - Self-referential hierarchy

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_category_parent ON category(parent_category_id);
- CREATE INDEX idx_category_slug ON category(slug);
- CREATE INDEX idx_category_path ON category(category_path);
- CREATE INDEX idx_category_order ON category(display_order);

SPECIAL CONSIDERATIONS:
- Use materialized path or closure table for deep hierarchies
- Consider using ltree extension for hierarchical queries
- Cache product counts and update on product changes
- Handle circular reference prevention in parent_category_id

SQL EXAMPLE - Hierarchy with Materialized Path:
CREATE TABLE category (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE,
    parent_id UUID REFERENCES category(id),
    path VARCHAR(1000), -- e.g., '/1/5/23/'
    level SMALLINT DEFAULT 0,
    CONSTRAINT no_self_reference CHECK (id != parent_id)
);

-- Recursive query for all subcategories
WITH RECURSIVE category_tree AS (
    SELECT id, name, parent_id, 0 as level
    FROM category WHERE parent_id IS NULL
    UNION ALL
    SELECT c.id, c.name, c.parent_id, ct.level + 1
    FROM category c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree;
""",
            resource_type="Category",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["category", "classification", "hierarchy", "taxonomy", "navigation"],
            trust_level=1.0
        ))
        
        # Order Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "order", "definition"),
            content="""
ENTITY: Order
DESCRIPTION: Represents a customer purchase transaction.

REQUIRED ATTRIBUTES:
- order_id: UUID PRIMARY KEY - Unique identifier
- order_number: VARCHAR(50) NOT NULL UNIQUE - Human-readable order number
- customer_id: UUID NOT NULL REFERENCES customer(id) - Buyer
- order_status: VARCHAR(50) NOT NULL DEFAULT 'pending' - Order status
- subtotal: DECIMAL(12,2) NOT NULL - Sum of line items
- total_amount: DECIMAL(12,2) NOT NULL - Final amount after tax/shipping
- order_date: TIMESTAMP WITH TIME ZONE DEFAULT NOW() - Order placement time
- created_at: TIMESTAMP WITH TIME ZONE - Record creation time

RECOMMENDED ATTRIBUTES:
- payment_status: VARCHAR(50) DEFAULT 'pending' - Payment state
- fulfillment_status: VARCHAR(50) DEFAULT 'unfulfilled' - Shipping state
- shipping_cost: DECIMAL(12,2) DEFAULT 0 - Shipping charges
- tax_amount: DECIMAL(12,2) DEFAULT 0 - Tax total
- discount_amount: DECIMAL(12,2) DEFAULT 0 - Discounts applied
- currency: CHAR(3) DEFAULT 'USD' - Currency code
- billing_address_id: UUID REFERENCES address(id) - Billing address
- shipping_address_id: UUID REFERENCES address(id) - Shipping address
- shipping_method: VARCHAR(100) - Selected shipping method
- coupon_code: VARCHAR(50) - Applied coupon
- notes: TEXT - Customer notes
- internal_notes: TEXT - Staff notes
- is_gift: BOOLEAN DEFAULT FALSE - Gift order flag
- gift_message: TEXT - Gift message
- ip_address: INET - Customer IP for fraud detection
- user_agent: TEXT - Browser info
- shipped_date: TIMESTAMP - When shipped
- delivered_date: TIMESTAMP - When delivered
- cancelled_date: TIMESTAMP - When cancelled
- cancellation_reason: TEXT - Reason for cancellation
- updated_at: TIMESTAMP WITH TIME ZONE - Last update

RELATIONSHIPS:
- Order N:1 Customer - Order belongs to customer
- Order 1:N OrderItem - Order contains line items
- Order 1:N Payment - Order has payments
- Order 1:N Shipment - Order has shipments
- Order N:1 Address (billing) - Billing address
- Order N:1 Address (shipping) - Shipping address
- Order N:1 Coupon - Applied coupon

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_order_number ON orders(order_number);
- CREATE INDEX idx_order_customer ON orders(customer_id);
- CREATE INDEX idx_order_status ON orders(order_status);
- CREATE INDEX idx_order_date ON orders(order_date);
- CREATE INDEX idx_order_payment_status ON orders(payment_status);

SPECIAL CONSIDERATIONS:
- Use 'orders' as table name (order is SQL reserved word)
- Generate sequential order_number for customer reference
- Store address snapshot, not just reference (addresses may change)
- Implement order state machine for status transitions
- Consider order versioning for audit trail
""",
            resource_type="Order",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["order", "purchase", "transaction", "sale", "checkout"],
            trust_level=1.0
        ))
        
        # OrderItem Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "order_item", "definition"),
            content="""
ENTITY: OrderItem (Order Line Item)
DESCRIPTION: Individual line item within an order.

REQUIRED ATTRIBUTES:
- order_item_id: UUID PRIMARY KEY - Unique identifier
- order_id: UUID NOT NULL REFERENCES orders(id) - Parent order
- product_id: UUID NOT NULL REFERENCES product(id) - Purchased product
- quantity: INTEGER NOT NULL CHECK (quantity > 0) - Quantity ordered
- unit_price: DECIMAL(12,2) NOT NULL - Price per unit at time of order
- line_total: DECIMAL(12,2) NOT NULL - quantity * unit_price

RECOMMENDED ATTRIBUTES:
- sku: VARCHAR(100) - Product SKU snapshot
- product_name: VARCHAR(255) - Product name snapshot
- variant_id: UUID REFERENCES product_variant(id) - Specific variant
- variant_name: VARCHAR(255) - Variant description (e.g., "Red, Large")
- discount_amount: DECIMAL(12,2) DEFAULT 0 - Line item discount
- tax_amount: DECIMAL(12,2) DEFAULT 0 - Line item tax
- weight: DECIMAL(10,3) - Item weight for shipping
- is_digital: BOOLEAN DEFAULT FALSE - Digital product flag
- download_url: VARCHAR(2048) - Download link for digital products
- download_count: INTEGER DEFAULT 0 - Times downloaded
- fulfillment_status: VARCHAR(50) - Item-level fulfillment
- notes: TEXT - Item-specific notes
- metadata: JSONB - Custom data
- created_at: TIMESTAMP WITH TIME ZONE - Creation time

RELATIONSHIPS:
- OrderItem N:1 Order - Item belongs to order
- OrderItem N:1 Product - Item references product
- OrderItem N:1 ProductVariant - Item may reference variant

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_orderitem_order ON order_item(order_id);
- CREATE INDEX idx_orderitem_product ON order_item(product_id);

SPECIAL CONSIDERATIONS:
- Store price/name snapshots (product data may change)
- line_total can be computed column or stored
- Support partial fulfillment at line level
- Consider bundle/kit support

SQL EXAMPLE:
CREATE TABLE order_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES product(id),
    sku VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12,2) NOT NULL,
    line_total DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
""",
            resource_type="OrderItem",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["order_item", "line_item", "order_line", "cart_item"],
            trust_level=1.0
        ))
        
        # Cart Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "cart", "definition"),
            content="""
ENTITY: Cart (Shopping Cart)
DESCRIPTION: Temporary storage for items before checkout.

REQUIRED ATTRIBUTES:
- cart_id: UUID PRIMARY KEY - Unique identifier
- created_at: TIMESTAMP WITH TIME ZONE - Cart creation time

RECOMMENDED ATTRIBUTES:
- customer_id: UUID REFERENCES customer(id) - Logged-in customer (nullable for guests)
- session_id: VARCHAR(255) - Session ID for guest carts
- cart_token: VARCHAR(255) UNIQUE - Unique token for cart recovery
- cart_status: VARCHAR(50) DEFAULT 'active' - active, converted, abandoned
- currency: CHAR(3) DEFAULT 'USD' - Cart currency
- subtotal: DECIMAL(12,2) DEFAULT 0 - Sum of items (cached)
- item_count: INTEGER DEFAULT 0 - Number of items (cached)
- coupon_code: VARCHAR(50) - Applied coupon
- discount_amount: DECIMAL(12,2) DEFAULT 0 - Discount applied
- expires_at: TIMESTAMP - Cart expiration time
- abandoned_at: TIMESTAMP - When marked as abandoned
- converted_at: TIMESTAMP - When converted to order
- last_activity_at: TIMESTAMP - Last user interaction
- ip_address: INET - User IP
- user_agent: TEXT - Browser info
- updated_at: TIMESTAMP WITH TIME ZONE - Last update

RELATIONSHIPS:
- Cart N:1 Customer - Cart belongs to customer (optional)
- Cart 1:N CartItem - Cart contains items
- Cart N:1 Coupon - Applied coupon

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_cart_customer ON cart(customer_id);
- CREATE INDEX idx_cart_session ON cart(session_id);
- CREATE INDEX idx_cart_token ON cart(cart_token);
- CREATE INDEX idx_cart_status ON cart(cart_status);
- CREATE INDEX idx_cart_abandoned ON cart(abandoned_at) WHERE cart_status = 'active';

SPECIAL CONSIDERATIONS:
- Support both guest and logged-in carts
- Merge guest cart on login
- Implement cart recovery emails for abandoned carts
- Consider cart expiration policy
- Update cached totals on item changes

SQL EXAMPLE:
CREATE TABLE cart (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customer(id) ON DELETE SET NULL,
    session_id VARCHAR(255),
    cart_token VARCHAR(255) UNIQUE DEFAULT encode(gen_random_bytes(32), 'hex'),
    status VARCHAR(50) DEFAULT 'active',
    subtotal DECIMAL(12,2) DEFAULT 0,
    item_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '30 days',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT cart_owner CHECK (customer_id IS NOT NULL OR session_id IS NOT NULL)
);
""",
            resource_type="Cart",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["cart", "shopping_cart", "basket", "checkout"],
            trust_level=1.0
        ))
        
        # Payment Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "payment", "definition"),
            content="""
ENTITY: Payment
DESCRIPTION: Payment transaction associated with an order.

REQUIRED ATTRIBUTES:
- payment_id: UUID PRIMARY KEY - Unique identifier
- order_id: UUID NOT NULL REFERENCES orders(id) - Associated order
- amount: DECIMAL(12,2) NOT NULL - Payment amount
- currency: CHAR(3) NOT NULL - Currency code
- payment_method: VARCHAR(50) NOT NULL - Payment method used
- status: VARCHAR(50) NOT NULL DEFAULT 'pending' - Payment status
- created_at: TIMESTAMP WITH TIME ZONE - Transaction time

RECOMMENDED ATTRIBUTES:
- payment_gateway: VARCHAR(100) - Gateway used (stripe, paypal)
- transaction_id: VARCHAR(255) - External transaction ID
- authorization_code: VARCHAR(100) - Auth code from gateway
- card_last_four: CHAR(4) - Last 4 digits of card
- card_brand: VARCHAR(50) - visa, mastercard, amex
- card_exp_month: SMALLINT - Card expiration month
- card_exp_year: SMALLINT - Card expiration year
- billing_address_id: UUID REFERENCES address(id) - Billing address
- payer_email: VARCHAR(255) - PayPal/gateway payer email
- refund_amount: DECIMAL(12,2) - Amount refunded
- refund_reason: TEXT - Reason for refund
- refund_date: TIMESTAMP - When refunded
- failure_reason: TEXT - Reason for failure
- gateway_response: JSONB - Full gateway response
- ip_address: INET - Customer IP
- metadata: JSONB - Additional data
- updated_at: TIMESTAMP WITH TIME ZONE - Last update

RELATIONSHIPS:
- Payment N:1 Order - Payment belongs to order
- Payment N:1 Address - Billing address

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_payment_order ON payment(order_id);
- CREATE INDEX idx_payment_status ON payment(status);
- CREATE INDEX idx_payment_transaction ON payment(transaction_id);
- CREATE INDEX idx_payment_date ON payment(created_at);

SPECIAL CONSIDERATIONS:
- Never store full card numbers (PCI compliance)
- Store gateway response for dispute resolution
- Support partial payments and refunds
- Implement idempotency for payment retries
- Consider payment audit logging

SQL EXAMPLE:
CREATE TABLE payment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    payment_method VARCHAR(50) NOT NULL,
    payment_gateway VARCHAR(100),
    transaction_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    card_last_four CHAR(4),
    card_brand VARCHAR(50),
    gateway_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
""",
            resource_type="Payment",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["payment", "transaction", "billing", "checkout"],
            trust_level=1.0
        ))
        
        # Inventory Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "inventory", "definition"),
            content="""
ENTITY: Inventory
DESCRIPTION: Stock tracking for products across warehouses/locations.

REQUIRED ATTRIBUTES:
- inventory_id: UUID PRIMARY KEY - Unique identifier
- product_id: UUID NOT NULL REFERENCES product(id) - Product being tracked
- warehouse_id: UUID NOT NULL REFERENCES warehouse(id) - Location
- quantity: INTEGER NOT NULL DEFAULT 0 - Current stock quantity

RECOMMENDED ATTRIBUTES:
- variant_id: UUID REFERENCES product_variant(id) - Specific variant
- sku: VARCHAR(100) - SKU for this location
- reserved_quantity: INTEGER DEFAULT 0 - Reserved for pending orders
- available_quantity: INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED
- min_stock_level: INTEGER DEFAULT 0 - Reorder point
- max_stock_level: INTEGER - Maximum capacity
- reorder_quantity: INTEGER - How much to reorder
- bin_location: VARCHAR(100) - Physical location in warehouse
- cost_per_unit: DECIMAL(12,2) - Cost for this batch
- last_counted_at: TIMESTAMP - Last physical count
- last_received_at: TIMESTAMP - Last stock received
- is_tracked: BOOLEAN DEFAULT TRUE - Track inventory
- updated_at: TIMESTAMP WITH TIME ZONE - Last update

RELATIONSHIPS:
- Inventory N:1 Product - Inventory tracks product
- Inventory N:1 Warehouse - Inventory in warehouse
- Inventory N:1 ProductVariant - May track specific variant

INDEXING RECOMMENDATIONS:
- CREATE UNIQUE INDEX idx_inventory_product_warehouse ON inventory(product_id, warehouse_id, COALESCE(variant_id, '00000000-0000-0000-0000-000000000000'));
- CREATE INDEX idx_inventory_low_stock ON inventory(product_id) WHERE quantity <= min_stock_level;
- CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);

SPECIAL CONSIDERATIONS:
- Use optimistic locking for concurrent updates
- Implement inventory reservations for pending orders
- Support multiple warehouses/locations
- Track inventory movements in separate log table
- Consider FIFO/LIFO for cost tracking

SQL EXAMPLE:
CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES product(id),
    warehouse_id UUID NOT NULL REFERENCES warehouse(id),
    variant_id UUID REFERENCES product_variant(id),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    reserved_quantity INTEGER NOT NULL DEFAULT 0 CHECK (reserved_quantity >= 0),
    min_stock_level INTEGER DEFAULT 0,
    bin_location VARCHAR(100),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(product_id, warehouse_id, variant_id)
);

-- Inventory movement log
CREATE TABLE inventory_movement (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID NOT NULL REFERENCES inventory(id),
    movement_type VARCHAR(50) NOT NULL, -- 'in', 'out', 'adjustment', 'transfer'
    quantity INTEGER NOT NULL,
    reference_type VARCHAR(50), -- 'order', 'return', 'purchase', 'count'
    reference_id UUID,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
""",
            resource_type="Inventory",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["inventory", "stock", "warehouse", "quantity"],
            trust_level=1.0
        ))
        
        # Review Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "review", "definition"),
            content="""
ENTITY: Review
DESCRIPTION: Customer review and rating for a product.

REQUIRED ATTRIBUTES:
- review_id: UUID PRIMARY KEY - Unique identifier
- product_id: UUID NOT NULL REFERENCES product(id) - Reviewed product
- rating: SMALLINT NOT NULL CHECK (rating >= 1 AND rating <= 5) - Star rating
- created_at: TIMESTAMP WITH TIME ZONE - Review submission time

RECOMMENDED ATTRIBUTES:
- customer_id: UUID REFERENCES customer(id) - Reviewer (nullable for imports)
- order_id: UUID REFERENCES orders(id) - Associated purchase
- review_title: VARCHAR(255) - Review headline
- review_text: TEXT - Review body
- pros: TEXT - Listed pros
- cons: TEXT - Listed cons
- status: VARCHAR(50) DEFAULT 'pending' - pending, approved, rejected
- is_verified_purchase: BOOLEAN DEFAULT FALSE - Purchased this product
- helpful_votes: INTEGER DEFAULT 0 - Upvotes
- unhelpful_votes: INTEGER DEFAULT 0 - Downvotes
- reported_count: INTEGER DEFAULT 0 - Times reported
- reviewer_name: VARCHAR(255) - Display name
- reviewer_email: VARCHAR(255) - For anonymous reviews
- images: JSONB - Review images
- response: TEXT - Seller response
- response_date: TIMESTAMP - When seller responded
- featured: BOOLEAN DEFAULT FALSE - Featured review
- updated_at: TIMESTAMP WITH TIME ZONE - Last update

RELATIONSHIPS:
- Review N:1 Product - Review for product
- Review N:1 Customer - Review by customer
- Review N:1 Order - Review from order

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_review_product ON review(product_id);
- CREATE INDEX idx_review_customer ON review(customer_id);
- CREATE INDEX idx_review_rating ON review(product_id, rating);
- CREATE INDEX idx_review_status ON review(status);
- CREATE INDEX idx_review_verified ON review(product_id) WHERE is_verified_purchase = TRUE;

SPECIAL CONSIDERATIONS:
- Validate verified_purchase against order history
- Implement review moderation workflow
- Calculate and cache average rating on product
- Support review images
- Handle review fraud detection

SQL EXAMPLE:
CREATE TABLE review (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    customer_id UUID REFERENCES customer(id) ON DELETE SET NULL,
    order_id UUID REFERENCES orders(id),
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(255),
    content TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    helpful_votes INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Update product average rating trigger
CREATE OR REPLACE FUNCTION update_product_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE product SET 
        avg_rating = (SELECT AVG(rating) FROM review WHERE product_id = NEW.product_id AND status = 'approved'),
        review_count = (SELECT COUNT(*) FROM review WHERE product_id = NEW.product_id AND status = 'approved')
    WHERE id = NEW.product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
""",
            resource_type="Review",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["review", "rating", "feedback", "testimonial"],
            trust_level=1.0
        ))
        
        # Coupon Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "coupon", "definition"),
            content="""
ENTITY: Coupon (Discount Code)
DESCRIPTION: Promotional discount codes for orders.

REQUIRED ATTRIBUTES:
- coupon_id: UUID PRIMARY KEY - Unique identifier
- coupon_code: VARCHAR(50) NOT NULL UNIQUE - Discount code
- discount_type: VARCHAR(50) NOT NULL - percentage, fixed_amount, free_shipping
- discount_value: DECIMAL(12,2) NOT NULL - Amount or percentage
- created_at: TIMESTAMP WITH TIME ZONE - Creation time

RECOMMENDED ATTRIBUTES:
- name: VARCHAR(255) - Internal coupon name
- description: TEXT - Coupon description
- discount_percentage: DECIMAL(5,2) - Percentage value
- min_purchase_amount: DECIMAL(12,2) - Minimum order value
- max_discount_amount: DECIMAL(12,2) - Cap on discount
- usage_limit: INTEGER - Total uses allowed
- usage_count: INTEGER DEFAULT 0 - Times used
- usage_limit_per_customer: INTEGER DEFAULT 1 - Uses per customer
- valid_from: TIMESTAMP WITH TIME ZONE - Start date
- valid_until: TIMESTAMP WITH TIME ZONE - Expiration date
- is_active: BOOLEAN DEFAULT TRUE - Active status
- applies_to: VARCHAR(50) - all, specific_products, specific_categories
- product_ids: UUID[] - Applicable products
- category_ids: UUID[] - Applicable categories
- excluded_product_ids: UUID[] - Excluded products
- customer_ids: UUID[] - Specific customers (private coupons)
- first_order_only: BOOLEAN DEFAULT FALSE - New customer only
- free_shipping: BOOLEAN DEFAULT FALSE - Includes free shipping
- stackable: BOOLEAN DEFAULT FALSE - Can combine with others
- metadata: JSONB - Additional rules
- updated_at: TIMESTAMP WITH TIME ZONE - Last update

RELATIONSHIPS:
- Coupon 1:N Order - Coupon used in orders
- Coupon M:N Product - Coupon applies to products
- Coupon M:N Category - Coupon applies to categories
- Coupon M:N Customer - Private coupons for customers

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_coupon_code ON coupon(coupon_code);
- CREATE INDEX idx_coupon_active ON coupon(is_active) WHERE is_active = TRUE;
- CREATE INDEX idx_coupon_dates ON coupon(valid_from, valid_until);

SPECIAL CONSIDERATIONS:
- Validate usage limits before applying
- Track usage per customer
- Support complex rules via metadata
- Handle timezone for validity dates
- Consider coupon stacking rules

SQL EXAMPLE:
CREATE TABLE coupon (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255),
    discount_type VARCHAR(50) NOT NULL CHECK (discount_type IN ('percentage', 'fixed_amount', 'free_shipping', 'buy_x_get_y')),
    discount_value DECIMAL(12,2) NOT NULL,
    min_purchase DECIMAL(12,2),
    max_discount DECIMAL(12,2),
    usage_limit INTEGER,
    usage_count INTEGER DEFAULT 0,
    per_customer_limit INTEGER DEFAULT 1,
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    first_order_only BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_dates CHECK (valid_from IS NULL OR valid_until IS NULL OR valid_from <= valid_until)
);

-- Track coupon usage per customer
CREATE TABLE coupon_usage (
    coupon_id UUID NOT NULL REFERENCES coupon(id),
    customer_id UUID NOT NULL REFERENCES customer(id),
    order_id UUID NOT NULL REFERENCES orders(id),
    used_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (coupon_id, order_id)
);
""",
            resource_type="Coupon",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["coupon", "discount", "promo", "promotion", "voucher"],
            trust_level=1.0
        ))
        
        # Address Entity
        entities.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "address", "definition"),
            content="""
ENTITY: Address
DESCRIPTION: Shipping or billing address for customers.

REQUIRED ATTRIBUTES:
- address_id: UUID PRIMARY KEY - Unique identifier
- address_line1: VARCHAR(255) NOT NULL - Street address
- city: VARCHAR(100) NOT NULL - City name
- country: VARCHAR(100) NOT NULL - Country name
- created_at: TIMESTAMP WITH TIME ZONE - Creation time

RECOMMENDED ATTRIBUTES:
- customer_id: UUID REFERENCES customer(id) - Owner (nullable for order snapshots)
- address_type: VARCHAR(50) DEFAULT 'shipping' - shipping, billing, both
- first_name: VARCHAR(100) - Recipient first name
- last_name: VARCHAR(100) - Recipient last name
- company: VARCHAR(255) - Company name
- address_line2: VARCHAR(255) - Apt, suite, unit
- state: VARCHAR(100) - State/province
- postal_code: VARCHAR(20) - ZIP/postal code
- country_code: CHAR(2) - ISO country code
- phone: VARCHAR(20) - Contact phone
- is_default: BOOLEAN DEFAULT FALSE - Default address
- is_billing_default: BOOLEAN DEFAULT FALSE - Default billing
- is_shipping_default: BOOLEAN DEFAULT FALSE - Default shipping
- latitude: DECIMAL(10,8) - Geocoded latitude
- longitude: DECIMAL(11,8) - Geocoded longitude
- verified: BOOLEAN DEFAULT FALSE - Address verified
- label: VARCHAR(50) - Home, Work, Other
- instructions: TEXT - Delivery instructions
- updated_at: TIMESTAMP WITH TIME ZONE - Last update

RELATIONSHIPS:
- Address N:1 Customer - Address belongs to customer
- Address 1:N Order (billing) - Billing address for orders
- Address 1:N Order (shipping) - Shipping address for orders

INDEXING RECOMMENDATIONS:
- CREATE INDEX idx_address_customer ON address(customer_id);
- CREATE INDEX idx_address_postal ON address(country_code, postal_code);
- CREATE INDEX idx_address_default ON address(customer_id) WHERE is_default = TRUE;

SPECIAL CONSIDERATIONS:
- Store address snapshot with orders (addresses may change)
- Support international address formats
- Consider address validation service integration
- Handle default address logic (only one default per customer)

SQL EXAMPLE:
CREATE TABLE address (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customer(id) ON DELETE CASCADE,
    type VARCHAR(50) DEFAULT 'shipping',
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company VARCHAR(255),
    line1 VARCHAR(255) NOT NULL,
    line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) NOT NULL,
    country_code CHAR(2),
    phone VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ensure only one default per customer
CREATE UNIQUE INDEX idx_address_single_default 
ON address(customer_id) 
WHERE is_default = TRUE;
""",
            resource_type="Address",
            chunk_type=ChunkType.DEFINITION,
            domain="ecommerce",
            tags=["address", "shipping", "billing", "location"],
            trust_level=1.0
        ))
        
        return entities
    
    def _get_relationship_patterns(self) -> List[RAGChunk]:
        """Get relationship pattern chunks with SQL examples."""
        patterns = []
        
        patterns.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "relationships", "customer_order"),
            content="""
RELATIONSHIP: Customer → Order (1:N)
DESCRIPTION: One customer places many orders over time.

CARDINALITY: 1:N (One-to-Many)
- One Customer can have 0 or more Orders
- Each Order belongs to exactly 1 Customer

SQL IMPLEMENTATION:
```sql
CREATE TABLE customer (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id UUID NOT NULL REFERENCES customer(id),
    total_amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    order_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_customer FOREIGN KEY (customer_id) 
        REFERENCES customer(id) ON DELETE RESTRICT
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
```

QUERY PATTERNS:
```sql
-- Get all orders for a customer
SELECT * FROM orders WHERE customer_id = :customer_id ORDER BY order_date DESC;

-- Get customer with order count
SELECT c.*, COUNT(o.id) as order_count, SUM(o.total_amount) as lifetime_value
FROM customer c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id;
```
""",
            resource_type="Relationship",
            chunk_type=ChunkType.PATTERN,
            domain="ecommerce",
            tags=["relationship", "customer", "order", "1:N"],
            trust_level=1.0
        ))
        
        patterns.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "relationships", "order_items"),
            content="""
RELATIONSHIP: Order → OrderItem (1:N)
DESCRIPTION: One order contains multiple line items.

CARDINALITY: 1:N (One-to-Many) with minimum 1
- Each Order must have at least 1 OrderItem
- Each OrderItem belongs to exactly 1 Order

SQL IMPLEMENTATION:
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) NOT NULL UNIQUE,
    customer_id UUID NOT NULL REFERENCES customer(id),
    subtotal DECIMAL(12,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE order_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES product(id),
    sku VARCHAR(100) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12,2) NOT NULL,
    line_total DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

CREATE INDEX idx_order_item_order ON order_item(order_id);
CREATE INDEX idx_order_item_product ON order_item(product_id);
```

QUERY PATTERNS:
```sql
-- Get order with all items
SELECT o.*, 
    json_agg(json_build_object(
        'sku', oi.sku,
        'name', oi.product_name,
        'quantity', oi.quantity,
        'price', oi.unit_price,
        'total', oi.line_total
    )) as items
FROM orders o
JOIN order_item oi ON o.id = oi.order_id
WHERE o.id = :order_id
GROUP BY o.id;
```
""",
            resource_type="Relationship",
            chunk_type=ChunkType.PATTERN,
            domain="ecommerce",
            tags=["relationship", "order", "order_item", "line_item", "1:N"],
            trust_level=1.0
        ))
        
        patterns.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "relationships", "product_category"),
            content="""
RELATIONSHIP: Product ↔ Category (M:N)
DESCRIPTION: Products can belong to multiple categories and categories contain multiple products.

CARDINALITY: M:N (Many-to-Many)
- One Product can be in 0 or more Categories
- One Category contains 0 or more Products

SQL IMPLEMENTATION:
```sql
CREATE TABLE category (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE,
    parent_id UUID REFERENCES category(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE product (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    -- Primary category for display
    primary_category_id UUID REFERENCES category(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Junction table for M:N relationship
CREATE TABLE product_category (
    product_id UUID NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES category(id) ON DELETE CASCADE,
    display_order INTEGER DEFAULT 0,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (product_id, category_id)
);

CREATE INDEX idx_product_category_cat ON product_category(category_id);
```

QUERY PATTERNS:
```sql
-- Get all categories for a product
SELECT c.* FROM category c
JOIN product_category pc ON c.id = pc.category_id
WHERE pc.product_id = :product_id;

-- Get all products in category (including subcategories)
WITH RECURSIVE category_tree AS (
    SELECT id FROM category WHERE id = :category_id
    UNION ALL
    SELECT c.id FROM category c
    JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT DISTINCT p.* FROM product p
JOIN product_category pc ON p.id = pc.product_id
WHERE pc.category_id IN (SELECT id FROM category_tree);
```
""",
            resource_type="Relationship",
            chunk_type=ChunkType.PATTERN,
            domain="ecommerce",
            tags=["relationship", "product", "category", "M:N", "junction"],
            trust_level=1.0
        ))
        
        patterns.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "relationships", "product_variant"),
            content="""
RELATIONSHIP: Product → ProductVariant (1:N)
DESCRIPTION: A product can have multiple variants (size, color combinations).

CARDINALITY: 1:N (One-to-Many)
- One Product can have 0 or more Variants
- Each Variant belongs to exactly 1 Product

SQL IMPLEMENTATION:
```sql
CREATE TABLE product (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    base_price DECIMAL(12,2) NOT NULL,
    has_variants BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE product_variant (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES product(id) ON DELETE CASCADE,
    sku VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255), -- e.g., "Red / Large"
    price DECIMAL(12,2), -- Override price, NULL = use base
    cost_price DECIMAL(12,2),
    stock_quantity INTEGER DEFAULT 0,
    weight DECIMAL(10,3),
    option1_name VARCHAR(100), -- e.g., "Color"
    option1_value VARCHAR(100), -- e.g., "Red"
    option2_name VARCHAR(100), -- e.g., "Size"
    option2_value VARCHAR(100), -- e.g., "Large"
    option3_name VARCHAR(100),
    option3_value VARCHAR(100),
    image_url VARCHAR(2048),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_variant_product ON product_variant(product_id);
CREATE INDEX idx_variant_options ON product_variant(product_id, option1_value, option2_value);
```

ALTERNATIVE: Separate Option Tables
```sql
-- For more flexible attribute management
CREATE TABLE product_option (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES product(id),
    name VARCHAR(100) NOT NULL, -- "Color", "Size"
    position INTEGER DEFAULT 0
);

CREATE TABLE product_option_value (
    id UUID PRIMARY KEY,
    option_id UUID NOT NULL REFERENCES product_option(id),
    value VARCHAR(100) NOT NULL, -- "Red", "Large"
    position INTEGER DEFAULT 0
);

CREATE TABLE product_variant (
    id UUID PRIMARY KEY,
    product_id UUID NOT NULL REFERENCES product(id),
    sku VARCHAR(100) UNIQUE,
    price DECIMAL(12,2),
    stock_quantity INTEGER DEFAULT 0
);

CREATE TABLE variant_option_value (
    variant_id UUID NOT NULL REFERENCES product_variant(id),
    option_value_id UUID NOT NULL REFERENCES product_option_value(id),
    PRIMARY KEY (variant_id, option_value_id)
);
```
""",
            resource_type="Relationship",
            chunk_type=ChunkType.PATTERN,
            domain="ecommerce",
            tags=["relationship", "product", "variant", "option", "1:N"],
            trust_level=1.0
        ))
        
        patterns.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "relationships", "cart_checkout"),
            content="""
RELATIONSHIP: Cart → Order (Conversion)
DESCRIPTION: Shopping cart converts to order at checkout.

CARDINALITY: 1:0..1 (Cart may or may not convert to Order)
- One Cart can become at most 1 Order
- Order references the original Cart (optional)

SQL IMPLEMENTATION:
```sql
CREATE TABLE cart (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customer(id),
    session_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active', -- active, converted, abandoned
    subtotal DECIMAL(12,2) DEFAULT 0,
    converted_to_order_id UUID, -- Populated after checkout
    converted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE cart_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cart_id UUID NOT NULL REFERENCES cart(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES product(id),
    variant_id UUID REFERENCES product_variant(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- On checkout, create order from cart
CREATE OR REPLACE FUNCTION checkout_cart(p_cart_id UUID, p_customer_id UUID)
RETURNS UUID AS $$
DECLARE
    v_order_id UUID;
BEGIN
    -- Create order
    INSERT INTO orders (customer_id, subtotal, total_amount, status)
    SELECT p_customer_id, c.subtotal, c.subtotal, 'pending'
    FROM cart c WHERE c.id = p_cart_id
    RETURNING id INTO v_order_id;
    
    -- Copy cart items to order items
    INSERT INTO order_item (order_id, product_id, sku, product_name, quantity, unit_price)
    SELECT v_order_id, ci.product_id, p.sku, p.name, ci.quantity, ci.unit_price
    FROM cart_item ci
    JOIN product p ON ci.product_id = p.id
    WHERE ci.cart_id = p_cart_id;
    
    -- Mark cart as converted
    UPDATE cart SET 
        status = 'converted',
        converted_to_order_id = v_order_id,
        converted_at = NOW()
    WHERE id = p_cart_id;
    
    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;
```
""",
            resource_type="Relationship",
            chunk_type=ChunkType.PATTERN,
            domain="ecommerce",
            tags=["relationship", "cart", "order", "checkout", "conversion"],
            trust_level=1.0
        ))
        
        return patterns
    
    def _get_datatype_guidelines(self) -> List[RAGChunk]:
        """Get PostgreSQL data type mapping guidelines."""
        return [RAGChunk(
            id=generate_chunk_id("ecommerce", "datatypes", "mapping"),
            content="""
E-COMMERCE POSTGRESQL DATA TYPE MAPPINGS

IDENTIFIERS:
- Primary keys: UUID PRIMARY KEY DEFAULT gen_random_uuid()
- Order numbers: VARCHAR(50) UNIQUE (human-readable sequence)
- SKU: VARCHAR(100) UNIQUE (alphanumeric product code)
- Slugs: VARCHAR(255) UNIQUE (URL-friendly identifier)

PRICING & MONEY:
- Prices: DECIMAL(12,2) - Always use DECIMAL, never FLOAT
- Currency: CHAR(3) - ISO 4217 code (USD, EUR)
- Tax rates: DECIMAL(5,4) - e.g., 0.0825 for 8.25%
- Quantities: INTEGER - Whole numbers for inventory
- Percentages: DECIMAL(5,2) - e.g., 15.50 for 15.5%

TEXT FIELDS:
- Names: VARCHAR(255)
- Short text: VARCHAR(500)
- Descriptions: TEXT
- Emails: VARCHAR(255)
- Phone numbers: VARCHAR(20)
- URLs: VARCHAR(2048)

DATES & TIMES:
- Timestamps: TIMESTAMP WITH TIME ZONE
- Dates only: DATE
- Expiration: TIMESTAMP WITH TIME ZONE
- Duration: INTERVAL

BOOLEANS:
- Flags: BOOLEAN DEFAULT FALSE
- Status flags: BOOLEAN (is_active, is_visible, is_featured)

ARRAYS & JSON:
- Tags: TEXT[] (PostgreSQL array)
- Flexible attributes: JSONB
- Image galleries: JSONB
- Metadata: JSONB

SPECIAL TYPES:
- IP addresses: INET
- Geographic: DECIMAL(10,8) lat, DECIMAL(11,8) lng
- Ratings: SMALLINT CHECK (rating BETWEEN 1 AND 5)

COMPUTED COLUMNS:
```sql
-- Line total
line_total DECIMAL(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED

-- Available inventory
available_qty INTEGER GENERATED ALWAYS AS (stock_qty - reserved_qty) STORED

-- Full name
full_name VARCHAR(201) GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED
```
""",
            resource_type="DataType",
            chunk_type=ChunkType.MAPPING,
            domain="ecommerce",
            tags=["datatype", "postgresql", "mapping", "types"],
            trust_level=1.0
        )]
    
    def _get_cardinality_rules(self) -> List[RAGChunk]:
        """Get cardinality rules for e-commerce relationships."""
        return [RAGChunk(
            id=generate_chunk_id("ecommerce", "cardinality", "rules"),
            content="""
E-COMMERCE CARDINALITY RULES AND SQL IMPLEMENTATIONS

0..1 (OPTIONAL SINGLE):
Use: Optional relationships, nullable foreign keys
Example: Product may have a sale price
```sql
sale_price DECIMAL(12,2), -- nullable, optional
discount_id UUID REFERENCES discount(id) -- optional discount
```

1..1 (REQUIRED SINGLE):
Use: Mandatory relationships
Example: Order must have a customer
```sql
customer_id UUID NOT NULL REFERENCES customer(id)
```

0..* (OPTIONAL MULTIPLE):
Use: Optional collections
Example: Product may have reviews
```sql
-- No constraint needed, just FK relationship
CREATE TABLE review (
    product_id UUID NOT NULL REFERENCES product(id)
);
-- Product can have 0 or more reviews
```

1..* (REQUIRED MULTIPLE):
Use: Must have at least one related record
Example: Order must have at least one item
```sql
-- Enforced at application level or with triggers
-- Because SQL can't enforce "at least one" directly

CREATE TABLE order_item (
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE
);

-- Application must ensure at least one item when creating order
```

N:1 (MANY-TO-ONE):
Use: Many records reference one parent
Example: Many products belong to one category
```sql
ALTER TABLE product ADD COLUMN category_id UUID REFERENCES category(id);
```

1:N (ONE-TO-MANY):
Use: Parent with many children
Example: Customer has many orders
```sql
CREATE TABLE orders (
    customer_id UUID NOT NULL REFERENCES customer(id)
);
```

M:N (MANY-TO-MANY):
Use: Both sides can have multiple relations
Example: Products and tags
```sql
CREATE TABLE product_tag (
    product_id UUID REFERENCES product(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tag(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, tag_id)
);
```

SELF-REFERENTIAL:
Use: Hierarchical data
Example: Category hierarchy
```sql
CREATE TABLE category (
    id UUID PRIMARY KEY,
    parent_id UUID REFERENCES category(id),
    CONSTRAINT no_self_ref CHECK (id != parent_id)
);
```
""",
            resource_type="Cardinality",
            chunk_type=ChunkType.CONSTRAINT,
            domain="ecommerce",
            tags=["cardinality", "relationship", "constraint", "rules"],
            trust_level=1.0
        )]
    
    def _get_normalization_rules(self) -> List[RAGChunk]:
        """Get normalization rules with e-commerce examples."""
        return [RAGChunk(
            id=generate_chunk_id("ecommerce", "normalization", "rules"),
            content="""
E-COMMERCE DATABASE NORMALIZATION RULES

FIRST NORMAL FORM (1NF):
Rule: Atomic values, no repeating groups

VIOLATION - Storing multiple values in one column:
```sql
-- BAD: Tags as comma-separated string
CREATE TABLE product (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    tags VARCHAR(1000) -- "electronics,sale,featured"
);
```

FIX - Use array or separate table:
```sql
-- GOOD: Using PostgreSQL array
CREATE TABLE product (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    tags TEXT[] -- ['electronics', 'sale', 'featured']
);

-- BETTER: Separate junction table for complex tag management
CREATE TABLE tag (id UUID PRIMARY KEY, name VARCHAR(100) UNIQUE);
CREATE TABLE product_tag (
    product_id UUID REFERENCES product(id),
    tag_id UUID REFERENCES tag(id),
    PRIMARY KEY (product_id, tag_id)
);
```

SECOND NORMAL FORM (2NF):
Rule: No partial dependencies on composite keys

VIOLATION - Partial dependency:
```sql
-- BAD: order_item with product details
CREATE TABLE order_item (
    order_id UUID,
    product_id UUID,
    quantity INTEGER,
    product_name VARCHAR(255), -- Depends only on product_id
    product_category VARCHAR(100), -- Depends only on product_id
    PRIMARY KEY (order_id, product_id)
);
```

FIX - Store only FK, join for details (with exception for snapshots):
```sql
-- GOOD for live data: Only store references
CREATE TABLE order_item (
    order_id UUID REFERENCES orders(id),
    product_id UUID REFERENCES product(id),
    quantity INTEGER,
    PRIMARY KEY (order_id, product_id)
);

-- EXCEPTION: Store snapshot for historical accuracy
CREATE TABLE order_item (
    id UUID PRIMARY KEY,
    order_id UUID REFERENCES orders(id),
    product_id UUID REFERENCES product(id),
    quantity INTEGER,
    -- Snapshots at time of purchase (intentional denormalization)
    sku_snapshot VARCHAR(100),
    name_snapshot VARCHAR(255),
    price_snapshot DECIMAL(12,2)
);
```

THIRD NORMAL FORM (3NF):
Rule: No transitive dependencies

VIOLATION - Transitive dependency:
```sql
-- BAD: Customer table with city and country details
CREATE TABLE customer (
    id UUID PRIMARY KEY,
    email VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    country_code CHAR(2),
    country_currency CHAR(3) -- Depends on country, not customer
);
```

FIX - Separate into related tables:
```sql
-- GOOD: Separate country table
CREATE TABLE country (
    code CHAR(2) PRIMARY KEY,
    name VARCHAR(100),
    currency CHAR(3)
);

CREATE TABLE customer (
    id UUID PRIMARY KEY,
    email VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country_code CHAR(2) REFERENCES country(code)
);
```

STRATEGIC DENORMALIZATION (When appropriate):

1. Cached aggregates for performance:
```sql
-- Cache frequently accessed counts
ALTER TABLE product ADD COLUMN review_count INTEGER DEFAULT 0;
ALTER TABLE product ADD COLUMN avg_rating DECIMAL(3,2);
ALTER TABLE category ADD COLUMN product_count INTEGER DEFAULT 0;
-- Update via triggers or scheduled jobs
```

2. Snapshots for historical accuracy:
```sql
-- Order must retain original pricing even if product changes
CREATE TABLE order_item (
    unit_price_snapshot DECIMAL(12,2) NOT NULL,
    product_name_snapshot VARCHAR(255) NOT NULL
);
```

3. Pre-computed for reporting:
```sql
-- Customer lifetime value
ALTER TABLE customer ADD COLUMN lifetime_value DECIMAL(12,2) DEFAULT 0;
```
""",
            resource_type="Normalization",
            chunk_type=ChunkType.RULE,
            domain="ecommerce",
            tags=["normalization", "1NF", "2NF", "3NF", "denormalization"],
            trust_level=1.0
        )]
    
    def _get_ecommerce_patterns(self) -> List[RAGChunk]:
        """Get e-commerce specific design patterns."""
        patterns = []
        
        patterns.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "patterns", "pricing"),
            content="""
E-COMMERCE DESIGN PATTERN: Dynamic Pricing

CHALLENGE: Products may have different prices based on customer type, quantity, time, etc.

SOLUTION: Price tiers and rules table
```sql
CREATE TABLE price_tier (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES product(id),
    name VARCHAR(100), -- "Wholesale", "VIP", "Bulk"
    customer_type VARCHAR(50), -- NULL for all customers
    min_quantity INTEGER DEFAULT 1,
    max_quantity INTEGER,
    price DECIMAL(12,2) NOT NULL,
    valid_from TIMESTAMP WITH TIME ZONE,
    valid_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0 -- Higher = checked first
);

CREATE INDEX idx_price_tier_product ON price_tier(product_id);
CREATE INDEX idx_price_tier_active ON price_tier(product_id, is_active) 
    WHERE is_active = TRUE;

-- Get best price for customer
CREATE OR REPLACE FUNCTION get_product_price(
    p_product_id UUID,
    p_customer_type VARCHAR,
    p_quantity INTEGER
) RETURNS DECIMAL AS $$
BEGIN
    RETURN (
        SELECT price FROM price_tier
        WHERE product_id = p_product_id
          AND is_active = TRUE
          AND (customer_type IS NULL OR customer_type = p_customer_type)
          AND min_quantity <= p_quantity
          AND (max_quantity IS NULL OR max_quantity >= p_quantity)
          AND (valid_from IS NULL OR valid_from <= NOW())
          AND (valid_until IS NULL OR valid_until >= NOW())
        ORDER BY priority DESC, price ASC
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql;
```
""",
            resource_type="Pattern",
            chunk_type=ChunkType.PATTERN,
            domain="ecommerce",
            tags=["pattern", "pricing", "tiers", "dynamic"],
            trust_level=1.0
        ))
        
        patterns.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "patterns", "inventory"),
            content="""
E-COMMERCE DESIGN PATTERN: Inventory Management

CHALLENGE: Track stock across multiple warehouses with reservations.

SOLUTION: Inventory with reservations and movement logging
```sql
CREATE TABLE warehouse (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    address_id UUID REFERENCES address(id),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES product(id),
    variant_id UUID REFERENCES product_variant(id),
    warehouse_id UUID NOT NULL REFERENCES warehouse(id),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    reserved INTEGER NOT NULL DEFAULT 0 CHECK (reserved >= 0),
    min_level INTEGER DEFAULT 0,
    bin_location VARCHAR(100),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (product_id, variant_id, warehouse_id)
);

-- Inventory reservation for pending orders
CREATE TABLE inventory_reservation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID NOT NULL REFERENCES inventory(id),
    order_id UUID NOT NULL REFERENCES orders(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    status VARCHAR(50) DEFAULT 'reserved', -- reserved, fulfilled, cancelled
    reserved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() + INTERVAL '30 minutes'
);

-- Movement log for audit
CREATE TABLE inventory_movement (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inventory_id UUID NOT NULL REFERENCES inventory(id),
    type VARCHAR(50) NOT NULL, -- 'purchase', 'sale', 'return', 'adjustment', 'transfer'
    quantity INTEGER NOT NULL, -- positive for in, negative for out
    reference_type VARCHAR(50),
    reference_id UUID,
    notes TEXT,
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Reserve inventory function
CREATE OR REPLACE FUNCTION reserve_inventory(
    p_product_id UUID,
    p_warehouse_id UUID,
    p_quantity INTEGER,
    p_order_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_inventory_id UUID;
    v_available INTEGER;
BEGIN
    SELECT id, quantity - reserved INTO v_inventory_id, v_available
    FROM inventory 
    WHERE product_id = p_product_id AND warehouse_id = p_warehouse_id
    FOR UPDATE;
    
    IF v_available >= p_quantity THEN
        UPDATE inventory SET reserved = reserved + p_quantity WHERE id = v_inventory_id;
        
        INSERT INTO inventory_reservation (inventory_id, order_id, quantity)
        VALUES (v_inventory_id, p_order_id, p_quantity);
        
        RETURN TRUE;
    END IF;
    
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;
```
""",
            resource_type="Pattern",
            chunk_type=ChunkType.PATTERN,
            domain="ecommerce",
            tags=["pattern", "inventory", "stock", "warehouse", "reservation"],
            trust_level=1.0
        ))
        
        patterns.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "patterns", "order_state"),
            content="""
E-COMMERCE DESIGN PATTERN: Order State Machine

CHALLENGE: Orders go through multiple states with valid transitions.

SOLUTION: State tracking with transition validation
```sql
-- Order status enum or lookup table
CREATE TABLE order_status (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_final BOOLEAN DEFAULT FALSE,
    display_order INTEGER
);

INSERT INTO order_status (code, name, is_final, display_order) VALUES
    ('pending', 'Pending', FALSE, 1),
    ('confirmed', 'Confirmed', FALSE, 2),
    ('processing', 'Processing', FALSE, 3),
    ('shipped', 'Shipped', FALSE, 4),
    ('delivered', 'Delivered', TRUE, 5),
    ('completed', 'Completed', TRUE, 6),
    ('cancelled', 'Cancelled', TRUE, 7),
    ('refunded', 'Refunded', TRUE, 8);

-- Valid state transitions
CREATE TABLE order_status_transition (
    from_status VARCHAR(50) REFERENCES order_status(code),
    to_status VARCHAR(50) REFERENCES order_status(code),
    requires_reason BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (from_status, to_status)
);

INSERT INTO order_status_transition (from_status, to_status) VALUES
    ('pending', 'confirmed'),
    ('pending', 'cancelled'),
    ('confirmed', 'processing'),
    ('confirmed', 'cancelled'),
    ('processing', 'shipped'),
    ('processing', 'cancelled'),
    ('shipped', 'delivered'),
    ('delivered', 'completed'),
    ('delivered', 'refunded');

-- Order status history
CREATE TABLE order_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id),
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    reason TEXT,
    changed_by UUID,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger to validate transitions
CREATE OR REPLACE FUNCTION validate_order_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        IF NOT EXISTS (
            SELECT 1 FROM order_status_transition
            WHERE from_status = OLD.status AND to_status = NEW.status
        ) THEN
            RAISE EXCEPTION 'Invalid status transition from % to %', OLD.status, NEW.status;
        END IF;
        
        INSERT INTO order_status_history (order_id, from_status, to_status)
        VALUES (NEW.id, OLD.status, NEW.status);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_order_status_change
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION validate_order_status_change();
```
""",
            resource_type="Pattern",
            chunk_type=ChunkType.PATTERN,
            domain="ecommerce",
            tags=["pattern", "order", "state_machine", "status", "workflow"],
            trust_level=1.0
        ))
        
        patterns.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "patterns", "search"),
            content="""
E-COMMERCE DESIGN PATTERN: Product Search

CHALLENGE: Fast, relevant product search with filtering.

SOLUTION: Full-text search with materialized search index
```sql
-- Add search vector to product
ALTER TABLE product ADD COLUMN search_vector tsvector;

-- Create GIN index for fast search
CREATE INDEX idx_product_search ON product USING gin(search_vector);

-- Update search vector on changes
CREATE OR REPLACE FUNCTION update_product_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.brand, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.short_description, '')), 'B') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'C') ||
        setweight(to_tsvector('english', COALESCE(array_to_string(NEW.tags, ' '), '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_product_search_vector
    BEFORE INSERT OR UPDATE ON product
    FOR EACH ROW
    EXECUTE FUNCTION update_product_search_vector();

-- Search function with ranking
CREATE OR REPLACE FUNCTION search_products(
    p_query TEXT,
    p_category_id UUID DEFAULT NULL,
    p_min_price DECIMAL DEFAULT NULL,
    p_max_price DECIMAL DEFAULT NULL,
    p_in_stock BOOLEAN DEFAULT NULL,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
) RETURNS TABLE (
    id UUID,
    name VARCHAR,
    price DECIMAL,
    image_url VARCHAR,
    rank REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id, p.name, p.price, p.image_url,
        ts_rank(p.search_vector, websearch_to_tsquery('english', p_query)) as rank
    FROM product p
    LEFT JOIN product_category pc ON p.id = pc.product_id
    WHERE p.is_visible = TRUE
      AND p.search_vector @@ websearch_to_tsquery('english', p_query)
      AND (p_category_id IS NULL OR pc.category_id = p_category_id)
      AND (p_min_price IS NULL OR p.price >= p_min_price)
      AND (p_max_price IS NULL OR p.price <= p_max_price)
      AND (p_in_stock IS NULL OR (p_in_stock = TRUE AND p.stock_status = 'in_stock'))
    ORDER BY rank DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Usage
SELECT * FROM search_products('wireless headphones', NULL, 50, 200, TRUE, 10, 0);
```
""",
            resource_type="Pattern",
            chunk_type=ChunkType.PATTERN,
            domain="ecommerce",
            tags=["pattern", "search", "full_text", "filter", "product_search"],
            trust_level=1.0
        ))
        
        patterns.append(RAGChunk(
            id=generate_chunk_id("ecommerce", "patterns", "audit"),
            content="""
E-COMMERCE DESIGN PATTERN: Audit Trail

CHALLENGE: Track all changes for compliance and debugging.

SOLUTION: Generic audit logging system
```sql
-- Audit log table
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    changed_fields TEXT[],
    user_id UUID,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);
CREATE INDEX idx_audit_user ON audit_log(user_id);

-- Generic audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB;
    v_new_data JSONB;
    v_changed_fields TEXT[];
    v_user_id UUID;
BEGIN
    -- Get user from session variable if set
    v_user_id := current_setting('app.current_user_id', TRUE)::UUID;
    
    IF TG_OP = 'INSERT' THEN
        v_new_data := to_jsonb(NEW);
        INSERT INTO audit_log (table_name, record_id, action, new_data, user_id)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', v_new_data, v_user_id);
        RETURN NEW;
        
    ELSIF TG_OP = 'UPDATE' THEN
        v_old_data := to_jsonb(OLD);
        v_new_data := to_jsonb(NEW);
        
        -- Find changed fields
        SELECT array_agg(key) INTO v_changed_fields
        FROM jsonb_each(v_old_data) o
        FULL OUTER JOIN jsonb_each(v_new_data) n USING (key)
        WHERE o.value IS DISTINCT FROM n.value;
        
        INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_fields, user_id)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', v_old_data, v_new_data, v_changed_fields, v_user_id);
        RETURN NEW;
        
    ELSIF TG_OP = 'DELETE' THEN
        v_old_data := to_jsonb(OLD);
        INSERT INTO audit_log (table_name, record_id, action, old_data, user_id)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', v_old_data, v_user_id);
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply to tables
CREATE TRIGGER audit_orders
    AFTER INSERT OR UPDATE OR DELETE ON orders
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

CREATE TRIGGER audit_product
    AFTER INSERT OR UPDATE OR DELETE ON product
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
```
""",
            resource_type="Pattern",
            chunk_type=ChunkType.PATTERN,
            domain="ecommerce",
            tags=["pattern", "audit", "logging", "history", "compliance"],
            trust_level=1.0
        ))
        
        return patterns
    
    def _get_constraint_rules(self) -> List[RAGChunk]:
        """Get constraint rules for e-commerce data validation."""
        return [RAGChunk(
            id=generate_chunk_id("ecommerce", "constraints", "validation"),
            content="""
E-COMMERCE CONSTRAINT RULES AND VALIDATIONS

CUSTOMER CONSTRAINTS:
```sql
ALTER TABLE customer
ADD CONSTRAINT chk_customer_email 
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z]{2,}$'),
ADD CONSTRAINT chk_customer_phone 
    CHECK (phone IS NULL OR phone ~ '^[+]?[0-9\\s\\-()]{7,20}$');
```

PRODUCT CONSTRAINTS:
```sql
ALTER TABLE product
ADD CONSTRAINT chk_product_price_positive 
    CHECK (price > 0),
ADD CONSTRAINT chk_product_sale_price 
    CHECK (sale_price IS NULL OR sale_price < price),
ADD CONSTRAINT chk_product_cost_price 
    CHECK (cost_price IS NULL OR cost_price <= price),
ADD CONSTRAINT chk_product_weight_positive 
    CHECK (weight IS NULL OR weight > 0),
ADD CONSTRAINT chk_product_sku_format 
    CHECK (sku ~ '^[A-Z0-9\\-_]{3,50}$');
```

ORDER CONSTRAINTS:
```sql
ALTER TABLE orders
ADD CONSTRAINT chk_order_amounts_positive 
    CHECK (subtotal >= 0 AND total_amount >= 0),
ADD CONSTRAINT chk_order_discount_valid 
    CHECK (discount_amount >= 0 AND discount_amount <= subtotal),
ADD CONSTRAINT chk_order_shipping_positive 
    CHECK (shipping_cost >= 0),
ADD CONSTRAINT chk_order_status_valid 
    CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'completed', 'cancelled', 'refunded'));
```

ORDER ITEM CONSTRAINTS:
```sql
ALTER TABLE order_item
ADD CONSTRAINT chk_orderitem_quantity_positive 
    CHECK (quantity > 0),
ADD CONSTRAINT chk_orderitem_price_positive 
    CHECK (unit_price > 0);
```

INVENTORY CONSTRAINTS:
```sql
ALTER TABLE inventory
ADD CONSTRAINT chk_inventory_quantity_nonnegative 
    CHECK (quantity >= 0),
ADD CONSTRAINT chk_inventory_reserved_valid 
    CHECK (reserved >= 0 AND reserved <= quantity);
```

REVIEW CONSTRAINTS:
```sql
ALTER TABLE review
ADD CONSTRAINT chk_review_rating_range 
    CHECK (rating >= 1 AND rating <= 5),
ADD CONSTRAINT chk_review_status_valid 
    CHECK (status IN ('pending', 'approved', 'rejected', 'flagged'));
```

COUPON CONSTRAINTS:
```sql
ALTER TABLE coupon
ADD CONSTRAINT chk_coupon_discount_positive 
    CHECK (discount_value > 0),
ADD CONSTRAINT chk_coupon_percentage_range 
    CHECK (discount_type != 'percentage' OR (discount_value > 0 AND discount_value <= 100)),
ADD CONSTRAINT chk_coupon_dates_valid 
    CHECK (valid_from IS NULL OR valid_until IS NULL OR valid_from <= valid_until),
ADD CONSTRAINT chk_coupon_usage_valid 
    CHECK (usage_limit IS NULL OR usage_count <= usage_limit);
```

PAYMENT CONSTRAINTS:
```sql
ALTER TABLE payment
ADD CONSTRAINT chk_payment_amount_positive 
    CHECK (amount > 0),
ADD CONSTRAINT chk_payment_refund_valid 
    CHECK (refund_amount IS NULL OR (refund_amount > 0 AND refund_amount <= amount)),
ADD CONSTRAINT chk_payment_card_last_four 
    CHECK (card_last_four IS NULL OR card_last_four ~ '^[0-9]{4}$'),
ADD CONSTRAINT chk_payment_method_valid 
    CHECK (payment_method IN ('credit_card', 'debit_card', 'paypal', 'stripe', 'bank_transfer', 'cash_on_delivery'));
```

ADDRESS CONSTRAINTS:
```sql
ALTER TABLE address
ADD CONSTRAINT chk_address_country_code 
    CHECK (country_code IS NULL OR country_code ~ '^[A-Z]{2}$'),
ADD CONSTRAINT chk_address_postal_code 
    CHECK (postal_code IS NULL OR LENGTH(postal_code) BETWEEN 3 AND 20);
```

CART CONSTRAINTS:
```sql
ALTER TABLE cart
ADD CONSTRAINT chk_cart_has_owner 
    CHECK (customer_id IS NOT NULL OR session_id IS NOT NULL),
ADD CONSTRAINT chk_cart_status_valid 
    CHECK (status IN ('active', 'converted', 'abandoned', 'expired'));
```

UNIQUE CONSTRAINTS:
```sql
-- Only one default address per customer
CREATE UNIQUE INDEX idx_customer_default_address 
    ON address(customer_id) WHERE is_default = TRUE;

-- Only one active cart per customer
CREATE UNIQUE INDEX idx_customer_active_cart 
    ON cart(customer_id) WHERE status = 'active' AND customer_id IS NOT NULL;

-- Unique order number
ALTER TABLE orders ADD CONSTRAINT uq_order_number UNIQUE (order_number);

-- Unique SKU
ALTER TABLE product ADD CONSTRAINT uq_product_sku UNIQUE (sku);
```
""",
            resource_type="Constraint",
            chunk_type=ChunkType.CONSTRAINT,
            domain="ecommerce",
            tags=["constraint", "validation", "check", "rules"],
            trust_level=1.0
        )]
