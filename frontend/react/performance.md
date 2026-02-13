# React Performance Guidelines

## Table of Contents
- [Overview](#overview)
- [React.memo](#reactmemo)
- [useMemo](#usememo)
- [useCallback](#usecallback)
- [Code Splitting](#code-splitting)
- [Lazy Loading](#lazy-loading)
- [Virtualization](#virtualization)
- [Profiling](#profiling)
- [Optimization Techniques](#optimization-techniques)
- [Best Practices](#best-practices)

## Overview

Performance optimization is crucial for creating fast, responsive React applications. Focus on measuring first, then optimizing based on real bottlenecks rather than premature optimization.

## React.memo

`React.memo` is a higher-order component that memoizes components to prevent unnecessary re-renders.

### Basic Usage

```jsx
import React, { memo } from 'react';

// Without memo - re-renders on every parent render
function ExpensiveComponent({ data }) {
  console.log('Rendering ExpensiveComponent');
  
  return (
    <div>
      {data.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
}

// With memo - only re-renders when props change
const MemoizedComponent = memo(function ExpensiveComponent({ data }) {
  console.log('Rendering ExpensiveComponent');
  
  return (
    <div>
      {data.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
    </div>
  );
});

// Usage
function Parent() {
  const [count, setCount] = useState(0);
  const data = [{ id: 1, name: 'Item 1' }];
  
  return (
    <div>
      <button onClick={() => setCount(count + 1)}>
        Count: {count}
      </button>
      {/* Won't re-render when count changes */}
      <MemoizedComponent data={data} />
    </div>
  );
}
```

### Custom Comparison Function

```jsx
const UserCard = memo(
  function UserCard({ user, settings }) {
    return (
      <div>
        <h3>{user.name}</h3>
        <p>{user.email}</p>
      </div>
    );
  },
  // Custom comparison function
  (prevProps, nextProps) => {
    // Return true if props are equal (skip re-render)
    // Return false if props are different (re-render)
    return (
      prevProps.user.id === nextProps.user.id &&
      prevProps.user.name === nextProps.user.name &&
      prevProps.user.email === nextProps.user.email
    );
  }
);

// Only compare specific fields
const Product = memo(
  ({ product }) => <div>{product.name} - ${product.price}</div>,
  (prev, next) => prev.product.id === next.product.id
);
```

### When to Use React.memo

```jsx
// Good candidates for memo:
// 1. Pure components that render often with same props
const ListItem = memo(({ item }) => {
  return <div>{item.name}</div>;
});

// 2. Large component trees
const ComplexDashboard = memo(({ data }) => {
  return (
    <div>
      <Chart data={data} />
      <Table data={data} />
      <Summary data={data} />
    </div>
  );
});

// 3. Components receiving stable props
const StaticSidebar = memo(({ items }) => {
  return (
    <nav>
      {items.map(item => <NavItem key={item.id} {...item} />)}
    </nav>
  );
});

// Don't use memo for:
// 1. Simple components
function SimpleButton({ onClick, children }) {
  return <button onClick={onClick}>{children}</button>;
}

// 2. Components that always receive different props
function Clock() {
  return <div>{new Date().toISOString()}</div>;
}
```

## useMemo

`useMemo` memoizes expensive computations.

### Basic Usage

```jsx
import { useMemo } from 'react';

function ProductList({ products, filters }) {
  // Expensive filtering operation
  const filteredProducts = useMemo(() => {
    console.log('Filtering products...');
    
    return products.filter(product => {
      return Object.entries(filters).every(([key, value]) => {
        if (!value) return true;
        return product[key] === value;
      });
    });
  }, [products, filters]); // Only recompute when these change
  
  return (
    <ul>
      {filteredProducts.map(product => (
        <li key={product.id}>{product.name}</li>
      ))}
    </ul>
  );
}
```

### Complex Calculations

```jsx
function DataAnalytics({ data }) {
  const statistics = useMemo(() => {
    console.log('Calculating statistics...');
    
    const sum = data.reduce((acc, val) => acc + val, 0);
    const avg = sum / data.length;
    const sorted = [...data].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];
    
    return { sum, avg, median };
  }, [data]);
  
  return (
    <div>
      <p>Sum: {statistics.sum}</p>
      <p>Average: {statistics.avg.toFixed(2)}</p>
      <p>Median: {statistics.median}</p>
    </div>
  );
}
```

### Memoizing Object References

```jsx
function Parent() {
  const [count, setCount] = useState(0);
  
  // Bad - new object on every render
  const config = { theme: 'dark', fontSize: 14 };
  
  // Good - memoized object
  const config = useMemo(() => ({
    theme: 'dark',
    fontSize: 14
  }), []); // Empty array = never changes
  
  return <Child config={config} />;
}

const Child = memo(({ config }) => {
  console.log('Child rendered');
  return <div style={{ fontSize: config.fontSize }}>Content</div>;
});
```

### Memoizing Array Operations

```jsx
function TodoList({ todos }) {
  const completedTodos = useMemo(() => {
    return todos.filter(todo => todo.completed);
  }, [todos]);
  
  const activeTodos = useMemo(() => {
    return todos.filter(todo => !todo.completed);
  }, [todos]);
  
  const sortedTodos = useMemo(() => {
    return [...todos].sort((a, b) => 
      new Date(b.createdAt) - new Date(a.createdAt)
    );
  }, [todos]);
  
  return (
    <div>
      <h3>Active: {activeTodos.length}</h3>
      <h3>Completed: {completedTodos.length}</h3>
      <ul>
        {sortedTodos.map(todo => (
          <li key={todo.id}>{todo.text}</li>
        ))}
      </ul>
    </div>
  );
}
```

## useCallback

`useCallback` memoizes functions to maintain referential equality.

### Basic Usage

```jsx
import { useCallback, memo } from 'react';

function Parent() {
  const [count, setCount] = useState(0);
  const [items, setItems] = useState([]);
  
  // Bad - new function on every render
  const handleClick = () => {
    console.log('Clicked');
  };
  
  // Good - memoized function
  const handleClick = useCallback(() => {
    console.log('Clicked');
  }, []); // No dependencies
  
  // With dependencies
  const handleAddItem = useCallback((item) => {
    setItems(prev => [...prev, item]);
  }, []); // setItems is stable, no need to include
  
  return (
    <div>
      <button onClick={() => setCount(count + 1)}>
        Count: {count}
      </button>
      <ExpensiveChild onClick={handleClick} />
    </div>
  );
}

const ExpensiveChild = memo(({ onClick }) => {
  console.log('ExpensiveChild rendered');
  return <button onClick={onClick}>Click me</button>;
});
```

### Event Handlers

```jsx
function TodoList({ todos }) {
  const [selectedId, setSelectedId] = useState(null);
  
  // Memoize handlers
  const handleSelect = useCallback((id) => {
    setSelectedId(id);
  }, []);
  
  const handleDelete = useCallback((id) => {
    // Call API to delete
    deleteTodo(id);
  }, []);
  
  const handleToggle = useCallback((id) => {
    // Call API to toggle
    toggleTodo(id);
  }, []);
  
  return (
    <ul>
      {todos.map(todo => (
        <TodoItem
          key={todo.id}
          todo={todo}
          onSelect={handleSelect}
          onDelete={handleDelete}
          onToggle={handleToggle}
        />
      ))}
    </ul>
  );
}

const TodoItem = memo(({ todo, onSelect, onDelete, onToggle }) => {
  console.log('TodoItem rendered:', todo.id);
  
  return (
    <li onClick={() => onSelect(todo.id)}>
      <input
        type="checkbox"
        checked={todo.completed}
        onChange={() => onToggle(todo.id)}
      />
      <span>{todo.text}</span>
      <button onClick={(e) => {
        e.stopPropagation();
        onDelete(todo.id);
      }}>
        Delete
      </button>
    </li>
  );
});
```

## Code Splitting

Code splitting breaks your bundle into smaller chunks that can be loaded on demand.

### Route-Based Splitting

```jsx
import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

// Lazy load route components
const Home = lazy(() => import('./pages/Home'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Profile = lazy(() => import('./pages/Profile'));
const Settings = lazy(() => import('./pages/Settings'));

function LoadingSpinner() {
  return (
    <div className="loading">
      <div className="spinner" />
      <p>Loading...</p>
    </div>
  );
}

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Suspense>
  );
}
```

### Component-Based Splitting

```jsx
import { lazy, Suspense } from 'react';

// Lazy load heavy components
const HeavyChart = lazy(() => import('./components/HeavyChart'));
const HeavyTable = lazy(() => import('./components/HeavyTable'));
const VideoPlayer = lazy(() => import('./components/VideoPlayer'));

function Dashboard() {
  const [showChart, setShowChart] = useState(false);
  
  return (
    <div>
      <h1>Dashboard</h1>
      
      <button onClick={() => setShowChart(!showChart)}>
        Toggle Chart
      </button>
      
      {showChart && (
        <Suspense fallback={<div>Loading chart...</div>}>
          <HeavyChart />
        </Suspense>
      )}
      
      <Suspense fallback={<div>Loading table...</div>}>
        <HeavyTable />
      </Suspense>
    </div>
  );
}
```

### Dynamic Imports

```jsx
function ImageGallery() {
  const [Lightbox, setLightbox] = useState(null);
  
  const handleImageClick = async () => {
    // Load component only when needed
    const module = await import('./components/Lightbox');
    setLightbox(() => module.default);
  };
  
  return (
    <div>
      <img src="thumb.jpg" onClick={handleImageClick} />
      
      {Lightbox && (
        <Suspense fallback={<div>Loading...</div>}>
          <Lightbox />
        </Suspense>
      )}
    </div>
  );
}
```

### Preloading Components

```jsx
import { lazy } from 'react';

// Preload on hover
const HeavyComponent = lazy(() => import('./HeavyComponent'));

let HeavyComponentPromise;

function preloadHeavyComponent() {
  if (!HeavyComponentPromise) {
    HeavyComponentPromise = import('./HeavyComponent');
  }
  return HeavyComponentPromise;
}

function App() {
  return (
    <button
      onMouseEnter={preloadHeavyComponent}
      onClick={() => setShowComponent(true)}
    >
      Show Component
    </button>
  );
}
```

## Lazy Loading

### Images

```jsx
function LazyImage({ src, alt, placeholder }) {
  const [imageSrc, setImageSrc] = useState(placeholder);
  const [imageRef, setImageRef] = useState(null);
  
  useEffect(() => {
    let observer;
    
    if (imageRef && 'IntersectionObserver' in window) {
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              setImageSrc(src);
              observer.unobserve(imageRef);
            }
          });
        },
        { threshold: 0.1 }
      );
      
      observer.observe(imageRef);
    } else {
      setImageSrc(src);
    }
    
    return () => {
      if (observer && imageRef) {
        observer.unobserve(imageRef);
      }
    };
  }, [imageRef, src]);
  
  return (
    <img
      ref={setImageRef}
      src={imageSrc}
      alt={alt}
      loading="lazy" // Native lazy loading
    />
  );
}
```

### Infinite Scroll

```jsx
function InfiniteList({ items, onLoadMore, hasMore, loading }) {
  const loadMoreRef = useRef();
  
  useEffect(() => {
    if (!hasMore || loading) return;
    
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          onLoadMore();
        }
      },
      { threshold: 1.0 }
    );
    
    const currentRef = loadMoreRef.current;
    if (currentRef) {
      observer.observe(currentRef);
    }
    
    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [hasMore, loading, onLoadMore]);
  
  return (
    <div>
      {items.map(item => (
        <div key={item.id}>{item.name}</div>
      ))}
      
      {hasMore && (
        <div ref={loadMoreRef}>
          {loading ? 'Loading...' : 'Load More'}
        </div>
      )}
    </div>
  );
}
```

## Virtualization

Virtualization renders only visible items in large lists.

### React Window

```jsx
import { FixedSizeList } from 'react-window';

function VirtualizedList({ items }) {
  const Row = ({ index, style }) => (
    <div style={style}>
      {items[index].name}
    </div>
  );
  
  return (
    <FixedSizeList
      height={600}
      itemCount={items.length}
      itemSize={50}
      width="100%"
    >
      {Row}
    </FixedSizeList>
  );
}

// Variable size list
import { VariableSizeList } from 'react-window';

function VariableList({ items }) {
  const getItemSize = (index) => {
    // Different heights based on content
    return items[index].height || 50;
  };
  
  const Row = ({ index, style }) => (
    <div style={style}>
      <h3>{items[index].title}</h3>
      <p>{items[index].description}</p>
    </div>
  );
  
  return (
    <VariableSizeList
      height={600}
      itemCount={items.length}
      itemSize={getItemSize}
      width="100%"
    >
      {Row}
    </VariableSizeList>
  );
}
```

### Virtual Grid

```jsx
import { FixedSizeGrid } from 'react-window';

function VirtualGrid({ items, columns }) {
  const Cell = ({ columnIndex, rowIndex, style }) => {
    const index = rowIndex * columns + columnIndex;
    const item = items[index];
    
    if (!item) return null;
    
    return (
      <div style={style}>
        <img src={item.thumbnail} alt={item.name} />
        <p>{item.name}</p>
      </div>
    );
  };
  
  return (
    <FixedSizeGrid
      columnCount={columns}
      columnWidth={200}
      height={600}
      rowCount={Math.ceil(items.length / columns)}
      rowHeight={200}
      width={columns * 200}
    >
      {Cell}
    </FixedSizeGrid>
  );
}
```

## Profiling

### React DevTools Profiler

```jsx
// Record performance with DevTools
// 1. Open React DevTools
// 2. Go to Profiler tab
// 3. Click record
// 4. Interact with app
// 5. Stop recording
// 6. Analyze flame graph and ranked chart
```

### Profiler API

```jsx
import { Profiler } from 'react';

function onRenderCallback(
  id,
  phase,
  actualDuration,
  baseDuration,
  startTime,
  commitTime,
  interactions
) {
  console.log(`${id} took ${actualDuration}ms to render`);
  
  // Send to analytics
  analytics.track('component-render', {
    id,
    phase,
    actualDuration,
    baseDuration
  });
}

function App() {
  return (
    <Profiler id="App" onRender={onRenderCallback}>
      <Dashboard />
      <Sidebar />
    </Profiler>
  );
}

// Nested profilers
function Dashboard() {
  return (
    <div>
      <Profiler id="Header" onRender={onRenderCallback}>
        <Header />
      </Profiler>
      
      <Profiler id="Content" onRender={onRenderCallback}>
        <Content />
      </Profiler>
    </div>
  );
}
```

### Performance Monitoring

```jsx
function usePerformanceMonitor(componentName) {
  useEffect(() => {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      if (renderTime > 16) { // > 1 frame at 60fps
        console.warn(
          `${componentName} render took ${renderTime}ms`
        );
      }
    };
  });
}

function ExpensiveComponent() {
  usePerformanceMonitor('ExpensiveComponent');
  
  // Component logic
  return <div>Content</div>;
}
```

## Optimization Techniques

### Debouncing and Throttling

```jsx
import { useState, useCallback } from 'react';

// Debounce hook
function useDebounce(callback, delay) {
  const [timeoutId, setTimeoutId] = useState(null);
  
  const debouncedCallback = useCallback((...args) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
    
    const id = setTimeout(() => {
      callback(...args);
    }, delay);
    
    setTimeoutId(id);
  }, [callback, delay, timeoutId]);
  
  return debouncedCallback;
}

// Usage
function SearchBox() {
  const [query, setQuery] = useState('');
  
  const performSearch = useCallback((searchTerm) => {
    fetch(`/api/search?q=${searchTerm}`)
      .then(res => res.json())
      .then(console.log);
  }, []);
  
  const debouncedSearch = useDebounce(performSearch, 500);
  
  const handleChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    debouncedSearch(value);
  };
  
  return (
    <input
      value={query}
      onChange={handleChange}
      placeholder="Search..."
    />
  );
}

// Throttle hook
function useThrottle(callback, delay) {
  const [lastRun, setLastRun] = useState(Date.now());
  
  const throttledCallback = useCallback((...args) => {
    const now = Date.now();
    
    if (now - lastRun >= delay) {
      callback(...args);
      setLastRun(now);
    }
  }, [callback, delay, lastRun]);
  
  return throttledCallback;
}
```

### Avoiding Inline Functions

```jsx
// Bad - creates new function on every render
function List({ items }) {
  return (
    <ul>
      {items.map(item => (
        <li onClick={() => handleClick(item.id)}>
          {item.name}
        </li>
      ))}
    </ul>
  );
}

// Good - memoized handler
function List({ items }) {
  const handleClick = useCallback((id) => {
    console.log('Clicked:', id);
  }, []);
  
  return (
    <ul>
      {items.map(item => (
        <ListItem
          key={item.id}
          item={item}
          onClick={handleClick}
        />
      ))}
    </ul>
  );
}

const ListItem = memo(({ item, onClick }) => {
  return (
    <li onClick={() => onClick(item.id)}>
      {item.name}
    </li>
  );
});
```

### Avoiding Inline Styles

```jsx
// Bad - creates new object every render
function Component() {
  return (
    <div style={{ padding: 20, margin: 10 }}>
      Content
    </div>
  );
}

// Good - static styles
const containerStyle = { padding: 20, margin: 10 };

function Component() {
  return <div style={containerStyle}>Content</div>;
}

// Best - CSS classes
function Component() {
  return <div className="container">Content</div>;
}
```

### Optimizing Context

```jsx
// Bad - single context causes all consumers to re-render
const AppContext = createContext();

function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('light');
  const [settings, setSettings] = useState({});
  
  return (
    <AppContext.Provider value={{ 
      user, setUser, 
      theme, setTheme,
      settings, setSettings
    }}>
      {children}
    </AppContext.Provider>
  );
}

// Good - split contexts
const UserContext = createContext();
const ThemeContext = createContext();
const SettingsContext = createContext();

function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('light');
  const [settings, setSettings] = useState({});
  
  return (
    <UserContext.Provider value={{ user, setUser }}>
      <ThemeContext.Provider value={{ theme, setTheme }}>
        <SettingsContext.Provider value={{ settings, setSettings }}>
          {children}
        </SettingsContext.Provider>
      </ThemeContext.Provider>
    </UserContext.Provider>
  );
}
```

## Best Practices

### 1. Measure Before Optimizing

```jsx
// Use React DevTools Profiler first
// Identify actual bottlenecks
// Then optimize specific components
```

### 2. Optimize Expensive Operations

```jsx
// Good candidates for useMemo:
// - Complex calculations
// - Filtering/sorting large arrays
// - Creating derived data

const expensiveValue = useMemo(() => {
  return complexCalculation(data);
}, [data]);
```

### 3. Memoize Callbacks for Children

```jsx
// When passing callbacks to memoized children
const Parent = () => {
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);
  
  return <MemoizedChild onClick={handleClick} />;
};
```

### 4. Use Production Builds

```bash
# Development builds are slower
npm start

# Production builds are optimized
npm run build
```

### 5. Monitor Bundle Size

```bash
# Analyze bundle
npm run build
npx source-map-explorer 'build/static/js/*.js'

# Use webpack-bundle-analyzer
npm install --save-dev webpack-bundle-analyzer
```

### 6. Lazy Load Heavy Dependencies

```jsx
// Load only when needed
const Chart = lazy(() => import('heavy-chart-library'));

function Dashboard() {
  const [showChart, setShowChart] = useState(false);
  
  return (
    <div>
      {showChart && (
        <Suspense fallback={<Loading />}>
          <Chart />
        </Suspense>
      )}
    </div>
  );
}
```

### 7. Use Web Workers for Heavy Computations

```jsx
// worker.js
self.addEventListener('message', (e) => {
  const result = expensiveCalculation(e.data);
  self.postMessage(result);
});

// Component.jsx
function useWorker() {
  const [result, setResult] = useState(null);
  
  useEffect(() => {
    const worker = new Worker('worker.js');
    
    worker.addEventListener('message', (e) => {
      setResult(e.data);
    });
    
    worker.postMessage(data);
    
    return () => worker.terminate();
  }, [data]);
  
  return result;
}
```

### 8. Avoid Premature Optimization

```jsx
// Don't optimize everything
// Focus on components that:
// - Render frequently
// - Have expensive computations
// - Cause performance issues in profiler

// Simple components don't need optimization
function SimpleButton({ onClick, children }) {
  return <button onClick={onClick}>{children}</button>;
}
```
