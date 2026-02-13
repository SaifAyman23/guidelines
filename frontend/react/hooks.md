# React Hooks Guidelines

## Table of Contents
- [Overview](#overview)
- [useState](#usestate)
- [useEffect](#useeffect)
- [useContext](#usecontext)
- [useReducer](#usereducer)
- [useMemo](#usememo)
- [useCallback](#usecallback)
- [useRef](#useref)
- [useImperativeHandle](#useimperativehandle)
- [useLayoutEffect](#uselayouteffect)
- [useDebugValue](#usedebugvalue)
- [Custom Hooks](#custom-hooks)
- [Hook Rules](#hook-rules)
- [Best Practices](#best-practices)

## Overview

Hooks are functions that let you "hook into" React state and lifecycle features from functional components. They enable you to use state and other React features without writing classes.

## useState

`useState` is the most fundamental hook for managing component state.

### Basic Usage

```jsx
import React, { useState } from 'react';

function Counter() {
  const [count, setCount] = useState(0);
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <button onClick={() => setCount(count - 1)}>Decrement</button>
      <button onClick={() => setCount(0)}>Reset</button>
    </div>
  );
}
```

### Functional Updates

Use functional updates when the new state depends on the previous state.

```jsx
function Counter() {
  const [count, setCount] = useState(0);
  
  // Bad - may have stale closure issues
  const increment = () => setCount(count + 1);
  
  // Good - functional update ensures latest state
  const increment = () => setCount(prev => prev + 1);
  
  const incrementBy = (amount) => {
    setCount(prev => prev + amount);
  };
  
  return <button onClick={increment}>Count: {count}</button>;
}
```

### Multiple State Variables

```jsx
function Form() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [age, setAge] = useState(0);
  const [errors, setErrors] = useState({});
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    const newErrors = {};
    if (!name) newErrors.name = 'Name is required';
    if (!email) newErrors.email = 'Email is required';
    if (age < 18) newErrors.age = 'Must be 18 or older';
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    // Submit form
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input 
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Name"
      />
      {errors.name && <span>{errors.name}</span>}
      
      <input 
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      {errors.email && <span>{errors.email}</span>}
      
      <input 
        type="number"
        value={age}
        onChange={(e) => setAge(Number(e.target.value))}
        placeholder="Age"
      />
      {errors.age && <span>{errors.age}</span>}
      
      <button type="submit">Submit</button>
    </form>
  );
}
```

### Object State

```jsx
function UserProfile() {
  const [user, setUser] = useState({
    name: '',
    email: '',
    age: 0,
    preferences: {
      theme: 'light',
      notifications: true
    }
  });
  
  // Update top-level property
  const updateName = (name) => {
    setUser(prev => ({ ...prev, name }));
  };
  
  // Update nested property
  const updateTheme = (theme) => {
    setUser(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        theme
      }
    }));
  };
  
  // Generic update handler
  const handleChange = (field, value) => {
    setUser(prev => ({ ...prev, [field]: value }));
  };
  
  return (
    <div>
      <input 
        value={user.name}
        onChange={(e) => handleChange('name', e.target.value)}
      />
      <input 
        value={user.email}
        onChange={(e) => handleChange('email', e.target.value)}
      />
    </div>
  );
}
```

### Lazy Initialization

Use lazy initialization for expensive initial state calculations.

```jsx
function ExpensiveComponent() {
  // Bad - runs on every render
  const [state, setState] = useState(expensiveCalculation());
  
  // Good - only runs once on mount
  const [state, setState] = useState(() => expensiveCalculation());
  
  return <div>{state}</div>;
}

function TodoList() {
  // Load from localStorage only once
  const [todos, setTodos] = useState(() => {
    const saved = localStorage.getItem('todos');
    return saved ? JSON.parse(saved) : [];
  });
  
  return <div>{/* Render todos */}</div>;
}
```

## useEffect

`useEffect` lets you perform side effects in functional components.

### Basic Usage

```jsx
import React, { useState, useEffect } from 'react';

function DocumentTitle() {
  const [count, setCount] = useState(0);
  
  // Runs after every render
  useEffect(() => {
    document.title = `Count: ${count}`;
  });
  
  return (
    <button onClick={() => setCount(count + 1)}>
      Clicked {count} times
    </button>
  );
}
```

### Effect with Dependencies

```jsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Runs only when userId changes
  useEffect(() => {
    setLoading(true);
    
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => {
        setUser(data);
        setLoading(false);
      });
  }, [userId]); // Dependency array
  
  if (loading) return <div>Loading...</div>;
  return <div>{user?.name}</div>;
}
```

### Cleanup Function

```jsx
function Timer() {
  const [seconds, setSeconds] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setSeconds(prev => prev + 1);
    }, 1000);
    
    // Cleanup function - runs before next effect and on unmount
    return () => {
      clearInterval(interval);
    };
  }, []); // Empty array = run once on mount
  
  return <div>Seconds: {seconds}</div>;
}
```

### Multiple Effects

Separate concerns into different effects.

```jsx
function UserDashboard({ userId }) {
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  
  // Effect 1: Fetch user data
  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(setUser);
  }, [userId]);
  
  // Effect 2: Fetch user posts
  useEffect(() => {
    fetch(`/api/users/${userId}/posts`)
      .then(res => res.json())
      .then(setPosts);
  }, [userId]);
  
  // Effect 3: Update document title
  useEffect(() => {
    if (user) {
      document.title = `${user.name}'s Dashboard`;
    }
  }, [user]);
  
  return <div>{/* Render */}</div>;
}
```

### Async Effects

```jsx
function SearchResults({ query }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    // Can't make useEffect callback async directly
    // Create async function inside
    let isMounted = true;
    
    async function fetchResults() {
      setLoading(true);
      
      try {
        const response = await fetch(`/api/search?q=${query}`);
        const data = await response.json();
        
        // Only update if component is still mounted
        if (isMounted) {
          setResults(data);
        }
      } catch (error) {
        if (isMounted) {
          console.error(error);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    
    if (query) {
      fetchResults();
    } else {
      setResults([]);
      setLoading(false);
    }
    
    return () => {
      isMounted = false;
    };
  }, [query]);
  
  return <div>{/* Render results */}</div>;
}
```

### Event Listeners

```jsx
function WindowSize() {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  });
  
  useEffect(() => {
    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);
  
  return <div>{size.width} x {size.height}</div>;
}
```

## useContext

`useContext` lets you subscribe to React context without nesting.

### Basic Usage

```jsx
import React, { createContext, useContext, useState } from 'react';

// Create context
const ThemeContext = createContext();

// Provider component
function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  
  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };
  
  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

// Consumer component
function ThemedButton() {
  const { theme, toggleTheme } = useContext(ThemeContext);
  
  return (
    <button 
      className={`btn-${theme}`}
      onClick={toggleTheme}
    >
      Current theme: {theme}
    </button>
  );
}

// App
function App() {
  return (
    <ThemeProvider>
      <ThemedButton />
    </ThemeProvider>
  );
}
```

### Multiple Contexts

```jsx
const UserContext = createContext();
const ThemeContext = createContext();
const LanguageContext = createContext();

function App() {
  return (
    <UserProvider>
      <ThemeProvider>
        <LanguageProvider>
          <Dashboard />
        </LanguageProvider>
      </ThemeProvider>
    </UserProvider>
  );
}

function Dashboard() {
  const user = useContext(UserContext);
  const theme = useContext(ThemeContext);
  const language = useContext(LanguageContext);
  
  return <div>{/* Use all contexts */}</div>;
}
```

### Custom Hook for Context

```jsx
const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  
  const login = async (credentials) => {
    const response = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
    const userData = await response.json();
    setUser(userData);
  };
  
  const logout = () => {
    setUser(null);
  };
  
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook
export function useAuth() {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  
  return context;
}

// Usage
function LoginButton() {
  const { user, login, logout } = useAuth();
  
  if (user) {
    return <button onClick={logout}>Logout</button>;
  }
  
  return <button onClick={() => login({ username: 'user' })}>Login</button>;
}
```

## useReducer

`useReducer` is an alternative to `useState` for complex state logic.

### Basic Usage

```jsx
import React, { useReducer } from 'react';

// Reducer function
function counterReducer(state, action) {
  switch (action.type) {
    case 'INCREMENT':
      return { count: state.count + 1 };
    case 'DECREMENT':
      return { count: state.count - 1 };
    case 'RESET':
      return { count: 0 };
    case 'SET':
      return { count: action.payload };
    default:
      throw new Error(`Unknown action: ${action.type}`);
  }
}

function Counter() {
  const [state, dispatch] = useReducer(counterReducer, { count: 0 });
  
  return (
    <div>
      <p>Count: {state.count}</p>
      <button onClick={() => dispatch({ type: 'INCREMENT' })}>+</button>
      <button onClick={() => dispatch({ type: 'DECREMENT' })}>-</button>
      <button onClick={() => dispatch({ type: 'RESET' })}>Reset</button>
      <button onClick={() => dispatch({ type: 'SET', payload: 10 })}>
        Set to 10
      </button>
    </div>
  );
}
```

### Complex State Management

```jsx
const initialState = {
  todos: [],
  filter: 'all',
  loading: false,
  error: null
};

function todosReducer(state, action) {
  switch (action.type) {
    case 'ADD_TODO':
      return {
        ...state,
        todos: [...state.todos, action.payload]
      };
      
    case 'TOGGLE_TODO':
      return {
        ...state,
        todos: state.todos.map(todo =>
          todo.id === action.payload
            ? { ...todo, completed: !todo.completed }
            : todo
        )
      };
      
    case 'DELETE_TODO':
      return {
        ...state,
        todos: state.todos.filter(todo => todo.id !== action.payload)
      };
      
    case 'SET_FILTER':
      return {
        ...state,
        filter: action.payload
      };
      
    case 'FETCH_START':
      return {
        ...state,
        loading: true,
        error: null
      };
      
    case 'FETCH_SUCCESS':
      return {
        ...state,
        loading: false,
        todos: action.payload
      };
      
    case 'FETCH_ERROR':
      return {
        ...state,
        loading: false,
        error: action.payload
      };
      
    default:
      return state;
  }
}

function TodoApp() {
  const [state, dispatch] = useReducer(todosReducer, initialState);
  
  const addTodo = (text) => {
    dispatch({
      type: 'ADD_TODO',
      payload: {
        id: Date.now(),
        text,
        completed: false
      }
    });
  };
  
  const toggleTodo = (id) => {
    dispatch({ type: 'TOGGLE_TODO', payload: id });
  };
  
  return <div>{/* Render todos */}</div>;
}
```

### TypeScript with useReducer

```typescript
type State = {
  count: number;
  history: number[];
};

type Action =
  | { type: 'INCREMENT' }
  | { type: 'DECREMENT' }
  | { type: 'SET'; payload: number }
  | { type: 'RESET' };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'INCREMENT':
      return {
        count: state.count + 1,
        history: [...state.history, state.count + 1]
      };
    case 'DECREMENT':
      return {
        count: state.count - 1,
        history: [...state.history, state.count - 1]
      };
    case 'SET':
      return {
        count: action.payload,
        history: [...state.history, action.payload]
      };
    case 'RESET':
      return { count: 0, history: [0] };
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, {
    count: 0,
    history: [0]
  });
  
  return <div>{state.count}</div>;
}
```

## useMemo

`useMemo` memoizes expensive computations to avoid unnecessary recalculations.

### Basic Usage

```jsx
import React, { useMemo, useState } from 'react';

function ExpensiveComponent({ items, filter }) {
  // Without useMemo - recalculates on every render
  const filteredItems = items.filter(item => item.category === filter);
  
  // With useMemo - only recalculates when dependencies change
  const filteredItems = useMemo(() => {
    console.log('Filtering items...');
    return items.filter(item => item.category === filter);
  }, [items, filter]);
  
  return (
    <ul>
      {filteredItems.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
}
```

### Complex Calculations

```jsx
function DataAnalysis({ data }) {
  const statistics = useMemo(() => {
    console.log('Calculating statistics...');
    
    const sum = data.reduce((acc, val) => acc + val, 0);
    const avg = sum / data.length;
    const sorted = [...data].sort((a, b) => a - b);
    const median = sorted[Math.floor(sorted.length / 2)];
    const min = Math.min(...data);
    const max = Math.max(...data);
    
    return { sum, avg, median, min, max };
  }, [data]);
  
  return (
    <div>
      <p>Sum: {statistics.sum}</p>
      <p>Average: {statistics.avg}</p>
      <p>Median: {statistics.median}</p>
      <p>Min: {statistics.min}</p>
      <p>Max: {statistics.max}</p>
    </div>
  );
}
```

### Memoizing Object References

```jsx
function Parent() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState('');
  
  // Bad - new object on every render
  const user = { name, timestamp: Date.now() };
  
  // Good - memoized object
  const user = useMemo(() => ({
    name,
    timestamp: Date.now()
  }), [name]);
  
  return <Child user={user} />;
}

const Child = React.memo(({ user }) => {
  console.log('Child rendered');
  return <div>{user.name}</div>;
});
```

## useCallback

`useCallback` memoizes functions to prevent unnecessary re-renders.

### Basic Usage

```jsx
import React, { useState, useCallback } from 'react';

function Parent() {
  const [count, setCount] = useState(0);
  const [name, setName] = useState('');
  
  // Bad - new function on every render
  const handleClick = () => {
    console.log('Clicked');
  };
  
  // Good - memoized function
  const handleClick = useCallback(() => {
    console.log('Clicked');
  }, []); // No dependencies
  
  // With dependencies
  const handleSubmit = useCallback(() => {
    console.log(`Submitting ${name}`);
  }, [name]); // Recreates when name changes
  
  return (
    <div>
      <Child onClick={handleClick} />
      <input value={name} onChange={(e) => setName(e.target.value)} />
    </div>
  );
}

const Child = React.memo(({ onClick }) => {
  console.log('Child rendered');
  return <button onClick={onClick}>Click me</button>;
});
```

### Event Handlers

```jsx
function TodoList({ todos }) {
  const [selectedId, setSelectedId] = useState(null);
  
  // Memoized event handler
  const handleSelect = useCallback((id) => {
    setSelectedId(id);
  }, []);
  
  const handleDelete = useCallback((id) => {
    // Delete logic
  }, []);
  
  return (
    <ul>
      {todos.map(todo => (
        <TodoItem
          key={todo.id}
          todo={todo}
          onSelect={handleSelect}
          onDelete={handleDelete}
        />
      ))}
    </ul>
  );
}

const TodoItem = React.memo(({ todo, onSelect, onDelete }) => {
  console.log('TodoItem rendered:', todo.id);
  
  return (
    <li>
      <span onClick={() => onSelect(todo.id)}>{todo.text}</span>
      <button onClick={() => onDelete(todo.id)}>Delete</button>
    </li>
  );
});
```

### useCallback vs useMemo

```jsx
// useCallback for functions
const handleClick = useCallback(() => {
  console.log('clicked');
}, []);

// Equivalent with useMemo
const handleClick = useMemo(() => {
  return () => console.log('clicked');
}, []);

// useMemo for values
const value = useMemo(() => computeExpensiveValue(a, b), [a, b]);

// useCallback is syntactic sugar for useMemo with functions
const callback = useCallback((arg) => doSomething(arg), []);
// Is the same as:
const callback = useMemo(() => (arg) => doSomething(arg), []);
```

## useRef

`useRef` creates a mutable reference that persists across re-renders.

### DOM References

```jsx
import React, { useRef, useEffect } from 'react';

function TextInput() {
  const inputRef = useRef(null);
  
  useEffect(() => {
    // Focus input on mount
    inputRef.current?.focus();
  }, []);
  
  const handleClick = () => {
    // Access DOM element
    inputRef.current?.select();
  };
  
  return (
    <div>
      <input ref={inputRef} type="text" />
      <button onClick={handleClick}>Select Text</button>
    </div>
  );
}
```

### Storing Mutable Values

```jsx
function Timer() {
  const [count, setCount] = useState(0);
  const intervalRef = useRef(null);
  
  const startTimer = () => {
    if (intervalRef.current) return; // Already running
    
    intervalRef.current = setInterval(() => {
      setCount(c => c + 1);
    }, 1000);
  };
  
  const stopTimer = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };
  
  useEffect(() => {
    return () => stopTimer(); // Cleanup on unmount
  }, []);
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={startTimer}>Start</button>
      <button onClick={stopTimer}>Stop</button>
    </div>
  );
}
```

### Previous Value

```jsx
function usePrevious(value) {
  const ref = useRef();
  
  useEffect(() => {
    ref.current = value;
  }, [value]);
  
  return ref.current;
}

// Usage
function Counter({ count }) {
  const previousCount = usePrevious(count);
  
  return (
    <div>
      <p>Current: {count}</p>
      <p>Previous: {previousCount}</p>
    </div>
  );
}
```

### Avoiding Stale Closures

```jsx
function ChatRoom({ roomId }) {
  const [message, setMessage] = useState('');
  const latestMessage = useRef(message);
  
  useEffect(() => {
    latestMessage.current = message;
  }, [message]);
  
  useEffect(() => {
    const timer = setInterval(() => {
      // Always has latest message
      console.log(latestMessage.current);
    }, 1000);
    
    return () => clearInterval(timer);
  }, []); // No dependencies needed
  
  return (
    <input 
      value={message}
      onChange={(e) => setMessage(e.target.value)}
    />
  );
}
```

## useImperativeHandle

`useImperativeHandle` customizes the instance value exposed when using `ref`.

```jsx
import React, { 
  useRef, 
  useImperativeHandle, 
  forwardRef 
} from 'react';

const FancyInput = forwardRef((props, ref) => {
  const inputRef = useRef();
  
  useImperativeHandle(ref, () => ({
    focus: () => {
      inputRef.current?.focus();
    },
    select: () => {
      inputRef.current?.select();
    },
    getValue: () => {
      return inputRef.current?.value;
    }
  }));
  
  return <input ref={inputRef} {...props} />;
});

// Usage
function Parent() {
  const inputRef = useRef();
  
  const handleClick = () => {
    inputRef.current?.focus();
    inputRef.current?.select();
    console.log(inputRef.current?.getValue());
  };
  
  return (
    <div>
      <FancyInput ref={inputRef} />
      <button onClick={handleClick}>Focus and Select</button>
    </div>
  );
}
```

## useLayoutEffect

`useLayoutEffect` fires synchronously after all DOM mutations but before paint.

```jsx
import React, { useState, useLayoutEffect, useRef } from 'react';

function Tooltip() {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const tooltipRef = useRef(null);
  
  // Use useLayoutEffect for DOM measurements
  useLayoutEffect(() => {
    const rect = tooltipRef.current?.getBoundingClientRect();
    
    // Adjust position if tooltip goes off screen
    if (rect) {
      const newX = rect.right > window.innerWidth 
        ? window.innerWidth - rect.width 
        : rect.left;
      const newY = rect.bottom > window.innerHeight
        ? window.innerHeight - rect.height
        : rect.top;
        
      setPosition({ x: newX, y: newY });
    }
  });
  
  return (
    <div 
      ref={tooltipRef}
      style={{ position: 'absolute', left: position.x, top: position.y }}
    >
      Tooltip content
    </div>
  );
}

// Use useEffect for side effects that don't need to block paint
// Use useLayoutEffect for DOM measurements and synchronous updates
```

## useDebugValue

`useDebugValue` displays a label for custom hooks in React DevTools.

```jsx
import { useDebugValue, useState, useEffect } from 'react';

function useFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetch(url)
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      });
  }, [url]);
  
  // Shows in DevTools
  useDebugValue(loading ? 'Loading...' : 'Loaded');
  
  // Format expensive values
  useDebugValue(data, data => {
    return data ? `${data.length} items` : 'No data';
  });
  
  return { data, loading };
}
```

## Custom Hooks

Custom hooks let you extract component logic into reusable functions.

### Basic Custom Hook

```jsx
import { useState, useEffect } from 'react';

function useLocalStorage(key, initialValue) {
  // Get initial value from localStorage
  const [value, setValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(error);
      return initialValue;
    }
  });
  
  // Update localStorage when value changes
  useEffect(() => {
    try {
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error(error);
    }
  }, [key, value]);
  
  return [value, setValue];
}

// Usage
function App() {
  const [name, setName] = useLocalStorage('name', 'Guest');
  
  return (
    <input 
      value={name}
      onChange={(e) => setName(e.target.value)}
    />
  );
}
```

### Fetch Hook

```jsx
function useFetch(url, options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    let isMounted = true;
    
    async function fetchData() {
      try {
        setLoading(true);
        const response = await fetch(url, options);
        const result = await response.json();
        
        if (isMounted) {
          setData(result);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          setError(err);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    
    fetchData();
    
    return () => {
      isMounted = false;
    };
  }, [url, JSON.stringify(options)]);
  
  return { data, loading, error };
}

// Usage
function UserList() {
  const { data: users, loading, error } = useFetch('/api/users');
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return (
    <ul>
      {users?.map(user => <li key={user.id}>{user.name}</li>)}
    </ul>
  );
}
```

### Form Hook

```jsx
function useForm(initialValues) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  
  const handleChange = (name, value) => {
    setValues(prev => ({ ...prev, [name]: value }));
  };
  
  const handleBlur = (name) => {
    setTouched(prev => ({ ...prev, [name]: true }));
  };
  
  const resetForm = () => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  };
  
  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    setErrors,
    resetForm
  };
}

// Usage
function LoginForm() {
  const { values, errors, handleChange, handleBlur, setErrors } = useForm({
    email: '',
    password: ''
  });
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    const newErrors = {};
    if (!values.email) newErrors.email = 'Required';
    if (!values.password) newErrors.password = 'Required';
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    // Submit form
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input 
        type="email"
        value={values.email}
        onChange={(e) => handleChange('email', e.target.value)}
        onBlur={() => handleBlur('email')}
      />
      {errors.email && <span>{errors.email}</span>}
      
      <input 
        type="password"
        value={values.password}
        onChange={(e) => handleChange('password', e.target.value)}
        onBlur={() => handleBlur('password')}
      />
      {errors.password && <span>{errors.password}</span>}
      
      <button type="submit">Login</button>
    </form>
  );
}
```

### Debounce Hook

```jsx
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);
  
  return debouncedValue;
}

// Usage
function SearchComponent() {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 500);
  
  useEffect(() => {
    if (debouncedSearchTerm) {
      // Perform search
      fetch(`/api/search?q=${debouncedSearchTerm}`)
        .then(res => res.json())
        .then(console.log);
    }
  }, [debouncedSearchTerm]);
  
  return (
    <input 
      value={searchTerm}
      onChange={(e) => setSearchTerm(e.target.value)}
      placeholder="Search..."
    />
  );
}
```

### Window Size Hook

```jsx
function useWindowSize() {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight
  });
  
  useEffect(() => {
    const handleResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight
      });
    };
    
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  return size;
}

// Usage
function ResponsiveComponent() {
  const { width } = useWindowSize();
  
  return (
    <div>
      {width < 768 ? <MobileView /> : <DesktopView />}
    </div>
  );
}
```

## Hook Rules

### 1. Only Call Hooks at the Top Level

```jsx
// Bad - conditional hook
function Component({ condition }) {
  if (condition) {
    const [state, setState] = useState(0); // ❌ Error!
  }
  
  return <div>{state}</div>;
}

// Good - hook at top level
function Component({ condition }) {
  const [state, setState] = useState(0); // ✅ Correct
  
  if (!condition) {
    return null;
  }
  
  return <div>{state}</div>;
}
```

### 2. Only Call Hooks from React Functions

```jsx
// Bad - hook in regular function
function calculateTotal(items) {
  const [total, setTotal] = useState(0); // ❌ Error!
  return total;
}

// Good - hook in React component
function Cart({ items }) {
  const [total, setTotal] = useState(0); // ✅ Correct
  
  return <div>{total}</div>;
}

// Good - hook in custom hook
function useTotal(items) {
  const [total, setTotal] = useState(0); // ✅ Correct
  return total;
}
```

## Best Practices

### 1. Use Descriptive Hook Names

```jsx
// Bad
const [s, setS] = useState(0);
const [d, setD] = useState(null);

// Good
const [score, setScore] = useState(0);
const [userData, setUserData] = useState(null);
```

### 2. Keep Effects Focused

```jsx
// Bad - one effect doing multiple things
useEffect(() => {
  fetchUser();
  updateTitle();
  setupWebSocket();
  trackAnalytics();
}, []);

// Good - separate effects
useEffect(() => {
  fetchUser();
}, []);

useEffect(() => {
  updateTitle();
}, [user]);

useEffect(() => {
  const ws = setupWebSocket();
  return () => ws.close();
}, []);

useEffect(() => {
  trackAnalytics();
}, [page]);
```

### 3. Properly Define Dependencies

```jsx
// Bad - missing dependencies
useEffect(() => {
  console.log(user.name);
}, []); // Should include 'user'

// Good - all dependencies listed
useEffect(() => {
  console.log(user.name);
}, [user]);

// Good - using ESLint plugin
// eslint-plugin-react-hooks will warn about missing dependencies
```

### 4. Clean Up Effects

```jsx
// Bad - no cleanup
useEffect(() => {
  const interval = setInterval(() => {
    console.log('tick');
  }, 1000);
}, []);

// Good - cleanup function
useEffect(() => {
  const interval = setInterval(() => {
    console.log('tick');
  }, 1000);
  
  return () => clearInterval(interval);
}, []);
```

### 5. Avoid Unnecessary Re-renders

```jsx
// Bad - creates new object every render
const config = { theme: 'dark', lang: 'en' };

// Good - memoize stable objects
const config = useMemo(() => ({
  theme: 'dark',
  lang: 'en'
}), []);

// Good - define outside component if truly constant
const CONFIG = { theme: 'dark', lang: 'en' };

function Component() {
  // Use CONFIG
}
```

### 6. Extract Custom Hooks for Reusability

```jsx
// Bad - duplicated logic
function ComponentA() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch('/api/data').then(r => r.json()).then(setData);
  }, []);
  return <div>{data}</div>;
}

function ComponentB() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch('/api/data').then(r => r.json()).then(setData);
  }, []);
  return <div>{data}</div>;
}

// Good - extracted custom hook
function useApiData() {
  const [data, setData] = useState(null);
  useEffect(() => {
    fetch('/api/data').then(r => r.json()).then(setData);
  }, []);
  return data;
}

function ComponentA() {
  const data = useApiData();
  return <div>{data}</div>;
}

function ComponentB() {
  const data = useApiData();
  return <div>{data}</div>;
}
```
