/**
 * Interactive Planogram Component - Phase 1: Visualization Only
 * Displays products in correct positions with proper stacking and gap detection
 */

class InteractivePlanogram extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            planogramData: null,
            loading: true,
            error: null,
            overlaySettings: {
                showNames: true,
                showPrices: true,
                showFacings: true,
                showConfidence: false,
                showStacking: true
            }
        };
    }

    async componentDidMount() {
        await this.loadPlanogramData();
    }

    async componentDidUpdate(prevProps) {
        if (prevProps.imageId !== this.props.imageId) {
            await this.loadPlanogramData();
        }
    }

    async loadPlanogramData() {
        if (!this.props.imageId) {
            this.setState({ loading: false, error: "No image selected" });
            return;
        }

        this.setState({ loading: true, error: null });

        try {
            const response = await fetch(`/api/planogram/${this.props.imageId}/editable`);
            
            if (!response.ok) {
                throw new Error(`Failed to load planogram data: ${response.statusText}`);
            }

            const data = await response.json();
            this.setState({ 
                planogramData: data,
                loading: false 
            });

        } catch (error) {
            console.error('Error loading planogram data:', error);
            this.setState({ 
                loading: false, 
                error: error.message 
            });
        }
    }

    toggleOverlay = (setting) => {
        this.setState(prevState => ({
            overlaySettings: {
                ...prevState.overlaySettings,
                [setting]: !prevState.overlaySettings[setting]
            }
        }));
    }

    renderLoadingState() {
        return (
            <div className="planogram-loading">
                <div className="loading-spinner"></div>
                <p>Loading planogram...</p>
            </div>
        );
    }

    renderErrorState() {
        return (
            <div className="planogram-error">
                <h3>❌ Failed to Load Planogram</h3>
                <p>{this.state.error}</p>
                <button 
                    className="btn btn-primary" 
                    onClick={() => this.loadPlanogramData()}
                >
                    🔄 Retry
                </button>
            </div>
        );
    }

    renderOverlayControls() {
        const { overlaySettings } = this.state;

        return (
            <div className="planogram-overlay-controls">
                <h4>Display Options</h4>
                <div className="overlay-toggles">
                    <label>
                        <input 
                            type="checkbox" 
                            checked={overlaySettings.showNames}
                            onChange={() => this.toggleOverlay('showNames')}
                        />
                        Product Names
                    </label>
                    <label>
                        <input 
                            type="checkbox" 
                            checked={overlaySettings.showPrices}
                            onChange={() => this.toggleOverlay('showPrices')}
                        />
                        Prices
                    </label>
                    <label>
                        <input 
                            type="checkbox" 
                            checked={overlaySettings.showFacings}
                            onChange={() => this.toggleOverlay('showFacings')}
                        />
                        Facing Counts
                    </label>
                    <label>
                        <input 
                            type="checkbox" 
                            checked={overlaySettings.showConfidence}
                            onChange={() => this.toggleOverlay('showConfidence')}
                        />
                        Confidence Scores
                    </label>
                    <label>
                        <input 
                            type="checkbox" 
                            checked={overlaySettings.showStacking}
                            onChange={() => this.toggleOverlay('showStacking')}
                        />
                        Stacking Indicators
                    </label>
                </div>
            </div>
        );
    }

    renderPlanogram() {
        const { planogramData } = this.state;
        const { planogram } = planogramData;
        const { shelves, metadata } = planogram;

        // Sort shelves from top to bottom (highest shelf number first)
        const sortedShelfNumbers = Object.keys(shelves)
            .map(num => parseInt(num))
            .sort((a, b) => b - a);

        return (
            <div className="interactive-planogram">
                {/* Planogram Header */}
                <div className="planogram-header">
                    <div className="planogram-stats">
                        <span className="stat">
                            📦 {planogram.total_products} Products
                        </span>
                        <span className="stat">
                            📚 {planogram.shelf_count} Shelves
                        </span>
                        <span className="stat">
                            🎯 {Math.round(metadata.extraction_confidence * 100)}% Confidence
                        </span>
                        {metadata.has_stacking && (
                            <span className="stat stacking-indicator">
                                📚 Stacking Detected
                            </span>
                        )}
                    </div>
                </div>

                {/* Shelf Container */}
                <div className="shelves-container">
                    {sortedShelfNumbers.map(shelfNum => (
                        <ShelfComponent
                            key={shelfNum}
                            shelfData={shelves[shelfNum]}
                            overlaySettings={this.state.overlaySettings}
                        />
                    ))}
                </div>

                {/* Overlay Controls */}
                {this.renderOverlayControls()}
            </div>
        );
    }

    render() {
        const { loading, error, planogramData } = this.state;

        if (loading) {
            return this.renderLoadingState();
        }

        if (error) {
            return this.renderErrorState();
        }

        if (!planogramData) {
            return (
                <div className="planogram-empty">
                    <p>No planogram data available</p>
                </div>
            );
        }

        return this.renderPlanogram();
    }
}

/**
 * Individual Shelf Component
 */
class ShelfComponent extends React.Component {
    renderSection(sectionName, sectionSlots) {
        if (!sectionSlots || sectionSlots.length === 0) {
            return null;
        }

        return (
            <div className={`shelf-section section-${sectionName.toLowerCase()}`}>
                <div className="section-label">{sectionName}</div>
                <div className="section-slots">
                    {sectionSlots.map((slot, index) => (
                        <SlotComponent
                            key={`${sectionName}-${slot.position}-${index}`}
                            slot={slot}
                            overlaySettings={this.props.overlaySettings}
                        />
                    ))}
                </div>
            </div>
        );
    }

    render() {
        const { shelfData } = this.props;
        const { shelf_number, sections, product_count, empty_count } = shelfData;

        return (
            <div className="shelf-component">
                {/* Shelf Header */}
                <div className="shelf-header">
                    <h3>Shelf {shelf_number}</h3>
                    <div className="shelf-stats">
                        <span className="products-count">{product_count} products</span>
                        {empty_count > 0 && (
                            <span className="gaps-count">{empty_count} gaps</span>
                        )}
                    </div>
                </div>

                {/* Shelf Content */}
                <div className="shelf-content">
                    {/* Render sections: Left, Center, Right */}
                    {this.renderSection("Left", sections.Left)}
                    {this.renderSection("Center", sections.Center)}
                    {this.renderSection("Right", sections.Right)}
                </div>
            </div>
        );
    }
}

/**
 * Individual Slot Component (Product or Empty)
 */
class SlotComponent extends React.Component {
    renderProductSlot() {
        const { slot, overlaySettings } = this.props;
        const { data: product } = slot;

        // Determine if product uses full height or is stacked
        const isStacked = !product.visual.uses_full_height;
        const stackRows = product.visual.stack_rows;

        if (isStacked) {
            // Render stacked products (multiple rows)
            return (
                <div className="product-slot stacked">
                    {Array.from({ length: stackRows }, (_, stackIndex) => (
                        <div 
                            key={stackIndex}
                            className={`stack-row stack-${stackIndex === 0 ? 'bottom' : 'top'}`}
                            style={{ backgroundColor: product.visual.confidence_color }}
                        >
                            <ProductContent 
                                product={product}
                                overlaySettings={overlaySettings}
                                stackIndex={stackIndex}
                                isStacked={true}
                            />
                        </div>
                    ))}
                </div>
            );
        } else {
            // Render full-height product
            return (
                <div 
                    className="product-slot full-height"
                    style={{ backgroundColor: product.visual.confidence_color }}
                >
                    <ProductContent 
                        product={product}
                        overlaySettings={overlaySettings}
                        isStacked={false}
                    />
                </div>
            );
        }
    }

    renderEmptySlot() {
        const { slot } = this.props;

        return (
            <div className="empty-slot">
                <div className="empty-content">
                    <span className="empty-icon">📭</span>
                    <span className="empty-text">Empty</span>
                </div>
            </div>
        );
    }

    render() {
        const { slot } = this.props;

        return (
            <div className={`slot-container position-${slot.position}`}>
                {slot.type === 'product' ? this.renderProductSlot() : this.renderEmptySlot()}
            </div>
        );
    }
}

/**
 * Product Content Component
 */
class ProductContent extends React.Component {
    render() {
        const { product, overlaySettings, stackIndex, isStacked } = this.props;

        return (
            <div className="product-content">
                {/* Product Name */}
                {overlaySettings.showNames && (
                    <div className="product-name">
                        {product.brand} {product.name}
                    </div>
                )}

                {/* Product Price */}
                {overlaySettings.showPrices && product.price && (
                    <div className="product-price">
                        £{product.price.toFixed(2)}
                    </div>
                )}

                {/* Facing Count */}
                {overlaySettings.showFacings && (
                    <div className="product-facings">
                        {product.quantity.total_facings} facings
                    </div>
                )}

                {/* Confidence Score */}
                {overlaySettings.showConfidence && (
                    <div className="product-confidence">
                        {Math.round(product.metadata.extraction_confidence * 100)}%
                    </div>
                )}

                {/* Stacking Indicator */}
                {overlaySettings.showStacking && isStacked && (
                    <div className="stacking-indicator">
                        Stack {stackIndex + 1}/{product.visual.stack_rows}
                    </div>
                )}
            </div>
        );
    }
}

// Export for use in main dashboard
window.InteractivePlanogram = InteractivePlanogram; 