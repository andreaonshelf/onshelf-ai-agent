/**
 * Interactive Planogram Component - Phase 1: Visualization Only
 * Displays products in correct positions with proper stacking and gap detection
 * Using React.createElement for browser compatibility (no JSX transpilation needed)
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
            },
            zoomLevel: 1.0
        };
        
        // Store reference for global controls
        window.currentPlanogramComponent = this;
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

    handleZoom = (factor, reset = false) => {
        this.setState(prevState => ({
            zoomLevel: reset ? 1.0 : prevState.zoomLevel * factor
        }));
    }

    renderLoadingState() {
        return React.createElement('div', { className: 'planogram-loading' },
            React.createElement('div', { className: 'loading-spinner' }),
            React.createElement('p', null, 'Loading planogram...')
        );
    }

    renderErrorState() {
        return React.createElement('div', { className: 'planogram-error' },
            React.createElement('h3', null, '❌ Failed to Load Planogram'),
            React.createElement('p', null, this.state.error),
            React.createElement('button', {
                className: 'btn btn-primary',
                onClick: () => this.loadPlanogramData()
            }, '🔄 Retry')
        );
    }

    renderOverlayControls() {
        const { overlaySettings } = this.state;

        return React.createElement('div', { className: 'planogram-overlay-controls' },
            React.createElement('h4', null, 'Display Options'),
            React.createElement('div', { className: 'overlay-toggles' },
                React.createElement('label', null,
                    React.createElement('input', {
                        type: 'checkbox',
                        checked: overlaySettings.showNames,
                        onChange: () => this.toggleOverlay('showNames')
                    }),
                    ' Product Names'
                ),
                React.createElement('label', null,
                    React.createElement('input', {
                        type: 'checkbox',
                        checked: overlaySettings.showPrices,
                        onChange: () => this.toggleOverlay('showPrices')
                    }),
                    ' Prices'
                ),
                React.createElement('label', null,
                    React.createElement('input', {
                        type: 'checkbox',
                        checked: overlaySettings.showFacings,
                        onChange: () => this.toggleOverlay('showFacings')
                    }),
                    ' Facing Counts'
                ),
                React.createElement('label', null,
                    React.createElement('input', {
                        type: 'checkbox',
                        checked: overlaySettings.showConfidence,
                        onChange: () => this.toggleOverlay('showConfidence')
                    }),
                    ' Confidence Scores'
                ),
                React.createElement('label', null,
                    React.createElement('input', {
                        type: 'checkbox',
                        checked: overlaySettings.showStacking,
                        onChange: () => this.toggleOverlay('showStacking')
                    }),
                    ' Stacking Indicators'
                )
            )
        );
    }

    renderPlanogram() {
        const { planogramData } = this.state;
        const { planogram } = planogramData;
        const { shelves } = planogram;

        // Sort shelves from top to bottom (highest shelf number first)
        const sortedShelfNumbers = Object.keys(shelves)
            .map(num => parseInt(num))
            .sort((a, b) => b - a);

        // Calculate total products and check for stacking
        let totalProducts = 0;
        let hasStacking = false;
        let avgConfidence = 0;
        let confidenceCount = 0;

        Object.values(shelves).forEach(shelf => {
            Object.values(shelf.sections).forEach(section => {
                section.forEach(slot => {
                    if (slot.type === 'product') {
                        totalProducts++;
                        if (slot.data.quantity.stack > 1) {
                            hasStacking = true;
                        }
                        if (slot.data.metadata && slot.data.metadata.extraction_confidence) {
                            avgConfidence += slot.data.metadata.extraction_confidence;
                            confidenceCount++;
                        }
                    }
                });
            });
        });

        avgConfidence = confidenceCount > 0 ? avgConfidence / confidenceCount : 0.9;

        return React.createElement('div', { 
            className: 'interactive-planogram',
            style: { transform: `scale(${this.state.zoomLevel})`, transformOrigin: 'top left' }
        },
            // Planogram Header
            React.createElement('div', { className: 'planogram-header' },
                React.createElement('div', { className: 'planogram-stats' },
                    React.createElement('span', { className: 'stat' }, `📦 ${totalProducts} Products`),
                    React.createElement('span', { className: 'stat' }, `📚 ${sortedShelfNumbers.length} Shelves`),
                    React.createElement('span', { className: 'stat' }, `🎯 ${Math.round(avgConfidence * 100)}% Confidence`),
                    hasStacking && React.createElement('span', { className: 'stat stacking-indicator' }, '📚 Stacking Detected')
                )
            ),

            // Shelf Container
            React.createElement('div', { className: 'shelves-container' },
                sortedShelfNumbers.map(shelfNum => 
                    React.createElement(ShelfComponent, {
                        key: shelfNum,
                        shelfData: shelves[shelfNum],
                        overlaySettings: this.state.overlaySettings
                    })
                )
            ),

            // Overlay Controls
            this.renderOverlayControls()
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
            return React.createElement('div', { className: 'planogram-empty' },
                React.createElement('p', null, 'No planogram data available')
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

        return React.createElement('div', { className: `shelf-section section-${sectionName.toLowerCase()}` },
            React.createElement('div', { className: 'section-label' }, sectionName),
            React.createElement('div', { className: 'section-slots' },
                sectionSlots.map((slot, index) => 
                    React.createElement(SlotComponent, {
                        key: `${sectionName}-${slot.position}-${index}`,
                        slot: slot,
                        overlaySettings: this.props.overlaySettings
                    })
                )
            )
        );
    }

    render() {
        const { shelfData } = this.props;
        const { shelf_number, sections, product_count, empty_count } = shelfData;

        return React.createElement('div', { className: 'shelf-component' },
            // Shelf Header
            React.createElement('div', { className: 'shelf-header' },
                React.createElement('h3', null, `Shelf ${shelf_number}`),
                React.createElement('div', { className: 'shelf-stats' },
                    React.createElement('span', { className: 'products-count' }, `${product_count} products`),
                    empty_count > 0 && React.createElement('span', { className: 'gaps-count' }, `${empty_count} gaps`)
                )
            ),

            // Shelf Content
            React.createElement('div', { className: 'shelf-content' },
                this.renderSection("Left", sections.Left),
                this.renderSection("Center", sections.Center),
                this.renderSection("Right", sections.Right)
            )
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
            return React.createElement('div', { className: 'product-slot stacked' },
                Array.from({ length: stackRows }, (_, stackIndex) => 
                    React.createElement('div', {
                        key: stackIndex,
                        className: `stack-row stack-${stackIndex === 0 ? 'bottom' : 'top'}`,
                        style: { backgroundColor: product.visual.confidence_color }
                    },
                        React.createElement(ProductContent, {
                            product: product,
                            overlaySettings: overlaySettings,
                            stackIndex: stackIndex,
                            isStacked: true
                        })
                    )
                )
            );
        } else {
            // Render full-height product
            return React.createElement('div', {
                className: 'product-slot full-height',
                style: { backgroundColor: product.visual.confidence_color }
            },
                React.createElement(ProductContent, {
                    product: product,
                    overlaySettings: overlaySettings,
                    isStacked: false
                })
            );
        }
    }

    renderEmptySlot() {
        return React.createElement('div', { className: 'empty-slot' },
            React.createElement('div', { className: 'empty-content' },
                React.createElement('span', { className: 'empty-icon' }, '📭'),
                React.createElement('span', { className: 'empty-text' }, 'Empty')
            )
        );
    }

    render() {
        const { slot } = this.props;

        return React.createElement('div', { className: `slot-container position-${slot.position}` },
            slot.type === 'product' ? this.renderProductSlot() : this.renderEmptySlot()
        );
    }
}

/**
 * Product Content Component
 */
class ProductContent extends React.Component {
    render() {
        const { product, overlaySettings, stackIndex, isStacked } = this.props;

        const elements = [];

        // Product Name
        if (overlaySettings.showNames) {
            elements.push(
                React.createElement('div', { 
                    key: 'name',
                    className: 'product-name' 
                }, `${product.brand} ${product.name}`)
            );
        }

        // Product Price
        if (overlaySettings.showPrices && product.price) {
            elements.push(
                React.createElement('div', { 
                    key: 'price',
                    className: 'product-price' 
                }, `£${product.price.toFixed(2)}`)
            );
        }

        // Facing Count
        if (overlaySettings.showFacings) {
            elements.push(
                React.createElement('div', { 
                    key: 'facings',
                    className: 'product-facings' 
                }, `${product.quantity.total_facings} facings`)
            );
        }

        // Confidence Score
        if (overlaySettings.showConfidence) {
            elements.push(
                React.createElement('div', { 
                    key: 'confidence',
                    className: 'product-confidence' 
                }, `${Math.round(product.metadata.extraction_confidence * 100)}%`)
            );
        }

        // Stacking Indicator
        if (overlaySettings.showStacking && isStacked) {
            elements.push(
                React.createElement('div', { 
                    key: 'stacking',
                    className: 'stacking-indicator' 
                }, `Stack ${stackIndex + 1}/${product.visual.stack_rows}`)
            );
        }

        return React.createElement('div', { className: 'product-content' }, ...elements);
    }
}

// Export for use in main dashboard
window.InteractivePlanogram = InteractivePlanogram; 