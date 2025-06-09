# Results Page Sidebar Implementation

## Overview
Added a collapsible sidebar with extraction list and filters to the Results page in the dashboard, allowing users to easily select and review specific extractions.

## Features Implemented

### 1. Collapsible Sidebar
- **Toggle Button**: Circular button with arrow icon to expand/collapse the sidebar
- **Smooth Transitions**: CSS transitions for smooth expand/collapse animation
- **Persistent State**: Sidebar state persists during the session

### 2. Filters Section
- **Status Filter**: All Status, Completed, Processing, Pending, Failed
- **Store Filter**: Dynamic list based on available extractions
- **Category Filter**: Dynamic list based on available extractions
- **Date Range**: From/To date inputs for filtering by creation date
- **Sort By**: Options for Newest First, Oldest First, Store Name
- **Clear Filters**: Button to reset all filters to default values

### 3. Extractions List
- **Real-time Updates**: Auto-refreshes every 10 seconds
- **Manual Refresh**: Refresh button in the header
- **Loading State**: Shows spinner while loading extractions
- **Item Display**: Shows store name, category, status, and product count
- **Timestamps**: Smart formatting (e.g., "5m ago", "2h ago", "3d ago")
- **Status Colors**: Visual indicators for different statuses
- **Selection State**: Highlights currently selected extraction

### 4. Responsive Design
- **Desktop**: Fixed sidebar width (320px, 280px on smaller screens)
- **Mobile**: Absolute positioned overlay with shadow
- **Grid Adjustment**: Results grid becomes single column on mobile

## Technical Implementation

### State Management
```javascript
const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
const [extractionsList, setExtractionsList] = useState([]);
const [filters, setFilters] = useState({
    status: 'all',
    store: 'all',
    category: 'all',
    dateFrom: '',
    dateTo: '',
    sortBy: 'date_desc'
});
const [availableStores, setAvailableStores] = useState([]);
const [availableCategories, setAvailableCategories] = useState([]);
const [sidebarLoading, setSidebarLoading] = useState(true);
```

### Key Functions
- `fetchExtractionsList()`: Fetches and filters extractions based on current filters
- `formatTimestamp()`: Converts timestamps to human-readable format
- Filter change handlers update state and trigger re-fetch

### API Integration
- Uses existing `/queue/items` endpoint with query parameters
- Supports filtering by status, store, category, and date range
- Limits results to 100 items for performance

## Usage
1. Navigate to the Results tab
2. Use filters to narrow down extractions
3. Click on any extraction in the list to view its details
4. Toggle sidebar visibility with the arrow button
5. Refresh the list manually or wait for auto-refresh

## Future Enhancements
- Search functionality for extractions
- Export filtered results
- Bulk actions on multiple extractions
- Advanced filtering options (e.g., by accuracy, cost)
- Pagination for large result sets