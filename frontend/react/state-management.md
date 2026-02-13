# React State Management Guidelines

## Table of Contents
- [Overview](#overview)
- [Local vs Global State](#local-vs-global-state)
- [State Lifting](#state-lifting)
- [Context API](#context-api)
- [Redux](#redux)
- [Zustand](#zustand)
- [Comparing Solutions](#comparing-solutions)
- [Best Practices](#best-practices)

## Overview

State management is one of the most critical aspects of React applications. Choosing the right state management solution depends on your application's complexity, team size, and specific requirements.

## Local vs Global State

### Local State

Local state is managed within a single component and doesn't need to be shared.

```jsx
import React, { useState } from 'react';

function Counter() {
  // Local state - only used in this component
  const [count, setCount] = useState(0);
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}
```

### When to Use Local State

- Form input values
- UI state (modals, dropdowns, tabs)
- Component-specific flags and toggles
- Temporary data that doesn't need to persist

### Global State

Global state is accessible throughout the application.

```jsx
import { createContext, useContext, useState } from 'react';

const UserContext = createContext();

function App() {
  const [user, setUser] = useState(null);
  
  return (
    <UserContext.Provider value={{ user, setUser }}>
      <Dashboard />
      <Profile />
    </UserContext.Provider>
  );
}

function Dashboard() {
  const { user } = useContext(UserContext);
  return <div>Welcome, {user?.name}</div>;
}
```

### When to Use Global State

- User authentication data
- Theme/locale settings
- Shopping cart items
- Data shared across multiple routes
- Application-wide configuration

## State Lifting

State lifting is moving state to the closest common ancestor when multiple components need to share it.

### Basic State Lifting

```jsx
// Before - duplicate state
function ComponentA() {
  const [user, setUser] = useState(null);
  return <div>{user?.name}</div>;
}

function ComponentB() {
  const [user, setUser] = useState(null);
  return <div>{user?.email}</div>;
}

// After - lifted state
function Parent() {
  const [user, setUser] = useState(null);
  
  return (
    <>
      <ComponentA user={user} />
      <ComponentB user={user} />
    </>
  );
}

function ComponentA({ user }) {
  return <div>{user?.name}</div>;
}

function ComponentB({ user }) {
  return <div>{user?.email}</div>;
}
```

### Complex State Lifting

```jsx
function ShoppingCart() {
  const [items, setItems] = useState([]);
  const [discountCode, setDiscountCode] = useState('');
  
  const addItem = (item) => {
    setItems(prev => [...prev, item]);
  };
  
  const removeItem = (id) => {
    setItems(prev => prev.filter(item => item.id !== id));
  };
  
  const updateQuantity = (id, quantity) => {
    setItems(prev => prev.map(item =>
      item.id === id ? { ...item, quantity } : item
    ));
  };
  
  const total = items.reduce((sum, item) => 
    sum + (item.price * item.quantity), 0
  );
  
  return (
    <div>
      <ProductList onAddItem={addItem} />
      <CartItems 
        items={items}
        onRemove={removeItem}
        onUpdateQuantity={updateQuantity}
      />
      <DiscountInput 
        code={discountCode}
        onChange={setDiscountCode}
      />
      <Total amount={total} discount={discountCode} />
    </div>
  );
}
```

## Context API

React's built-in solution for sharing state across components without prop drilling.

### Basic Context Setup

```jsx
import { createContext, useContext, useState } from 'react';

// 1. Create context
const ThemeContext = createContext();

// 2. Create provider component
export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  
  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };
  
  const value = {
    theme,
    toggleTheme
  };
  
  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

// 3. Create custom hook for consuming context
export function useTheme() {
  const context = useContext(ThemeContext);
  
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  
  return context;
}

// 4. Use in components
function ThemedButton() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <button className={`btn-${theme}`} onClick={toggleTheme}>
      Toggle Theme
    </button>
  );
}

// 5. Wrap app with provider
function App() {
  return (
    <ThemeProvider>
      <ThemedButton />
    </ThemeProvider>
  );
}
```

### Context with Reducer

```jsx
import { createContext, useContext, useReducer } from 'react';

// State and actions
const initialState = {
  todos: [],
  filter: 'all'
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
    default:
      return state;
  }
}

// Context
const TodosContext = createContext();

// Provider
export function TodosProvider({ children }) {
  const [state, dispatch] = useReducer(todosReducer, initialState);
  
  return (
    <TodosContext.Provider value={{ state, dispatch }}>
      {children}
    </TodosContext.Provider>
  );
}

// Custom hook
export function useTodos() {
  const context = useContext(TodosContext);
  
  if (!context) {
    throw new Error('useTodos must be used within TodosProvider');
  }
  
  return context;
}

// Usage in component
function TodoList() {
  const { state, dispatch } = useTodos();
  
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
  
  return (
    <div>
      {state.todos.map(todo => (
        <div key={todo.id} onClick={() => toggleTodo(todo.id)}>
          {todo.text}
        </div>
      ))}
    </div>
  );
}
```

### Multiple Contexts

```jsx
// auth-context.js
const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  
  const login = async (credentials) => {
    const userData = await api.login(credentials);
    setUser(userData);
  };
  
  const logout = () => setUser(null);
  
  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

// theme-context.js
const ThemeContext = createContext();

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);

// App.js
function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <Dashboard />
      </ThemeProvider>
    </AuthProvider>
  );
}

// Using multiple contexts
function Dashboard() {
  const { user } = useAuth();
  const { theme } = useTheme();
  
  return (
    <div className={`dashboard-${theme}`}>
      Welcome, {user?.name}
    </div>
  );
}
```

### Optimizing Context Performance

```jsx
import { createContext, useContext, useState, useMemo } from 'react';

// Split contexts for better performance
const UserStateContext = createContext();
const UserDispatchContext = createContext();

export function UserProvider({ children }) {
  const [user, setUser] = useState(null);
  
  // Memoize dispatch functions
  const dispatch = useMemo(() => ({
    login: async (credentials) => {
      const userData = await api.login(credentials);
      setUser(userData);
    },
    logout: () => setUser(null),
    updateProfile: (updates) => {
      setUser(prev => ({ ...prev, ...updates }));
    }
  }), []);
  
  return (
    <UserStateContext.Provider value={user}>
      <UserDispatchContext.Provider value={dispatch}>
        {children}
      </UserDispatchContext.Provider>
    </UserStateContext.Provider>
  );
}

// Separate hooks for state and dispatch
export const useUserState = () => {
  const context = useContext(UserStateContext);
  if (!context) throw new Error('Must be within UserProvider');
  return context;
};

export const useUserDispatch = () => {
  const context = useContext(UserDispatchContext);
  if (!context) throw new Error('Must be within UserProvider');
  return context;
};

// Components only re-render when their context changes
function UserProfile() {
  const user = useUserState(); // Re-renders when user changes
  return <div>{user?.name}</div>;
}

function LogoutButton() {
  const { logout } = useUserDispatch(); // Doesn't re-render when user changes
  return <button onClick={logout}>Logout</button>;
}
```

## Redux

Redux is a predictable state container that provides a centralized store for the entire application.

### Redux Setup

```bash
npm install @reduxjs/toolkit react-redux
```

### Creating a Redux Store

```javascript
// store.js
import { configureStore } from '@reduxjs/toolkit';
import todosReducer from './todosSlice';
import userReducer from './userSlice';

export const store = configureStore({
  reducer: {
    todos: todosReducer,
    user: userReducer
  }
});
```

### Creating a Slice

```javascript
// todosSlice.js
import { createSlice } from '@reduxjs/toolkit';

const todosSlice = createSlice({
  name: 'todos',
  initialState: {
    items: [],
    filter: 'all',
    loading: false,
    error: null
  },
  reducers: {
    addTodo: (state, action) => {
      state.items.push({
        id: Date.now(),
        text: action.payload,
        completed: false
      });
    },
    toggleTodo: (state, action) => {
      const todo = state.items.find(t => t.id === action.payload);
      if (todo) {
        todo.completed = !todo.completed;
      }
    },
    deleteTodo: (state, action) => {
      state.items = state.items.filter(t => t.id !== action.payload);
    },
    setFilter: (state, action) => {
      state.filter = action.payload;
    }
  }
});

export const { addTodo, toggleTodo, deleteTodo, setFilter } = todosSlice.actions;
export default todosSlice.reducer;
```

### Async Actions with Thunks

```javascript
// userSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// Async thunk
export const fetchUser = createAsyncThunk(
  'user/fetchUser',
  async (userId, { rejectWithValue }) => {
    try {
      const response = await fetch(`/api/users/${userId}`);
      const data = await response.json();
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const loginUser = createAsyncThunk(
  'user/login',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
      });
      
      if (!response.ok) {
        throw new Error('Login failed');
      }
      
      return await response.json();
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const userSlice = createSlice({
  name: 'user',
  initialState: {
    data: null,
    loading: false,
    error: null
  },
  reducers: {
    logout: (state) => {
      state.data = null;
    }
  },
  extraReducers: (builder) => {
    builder
      // fetchUser
      .addCase(fetchUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      // loginUser
      .addCase(loginUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  }
});

export const { logout } = userSlice.actions;
export default userSlice.reducer;
```

### Using Redux in Components

```jsx
// index.js
import { Provider } from 'react-redux';
import { store } from './store';

ReactDOM.render(
  <Provider store={store}>
    <App />
  </Provider>,
  document.getElementById('root')
);

// TodoList.js
import { useSelector, useDispatch } from 'react-redux';
import { addTodo, toggleTodo, deleteTodo, setFilter } from './todosSlice';

function TodoList() {
  const dispatch = useDispatch();
  
  // Select state
  const todos = useSelector(state => state.todos.items);
  const filter = useSelector(state => state.todos.filter);
  
  // Select with filtering
  const filteredTodos = useSelector(state => {
    const { items, filter } = state.todos;
    
    switch (filter) {
      case 'active':
        return items.filter(t => !t.completed);
      case 'completed':
        return items.filter(t => t.completed);
      default:
        return items;
    }
  });
  
  const handleAddTodo = (text) => {
    dispatch(addTodo(text));
  };
  
  const handleToggle = (id) => {
    dispatch(toggleTodo(id));
  };
  
  return (
    <div>
      <input onKeyPress={(e) => {
        if (e.key === 'Enter') {
          handleAddTodo(e.target.value);
          e.target.value = '';
        }
      }} />
      
      <div>
        <button onClick={() => dispatch(setFilter('all'))}>All</button>
        <button onClick={() => dispatch(setFilter('active'))}>Active</button>
        <button onClick={() => dispatch(setFilter('completed'))}>Completed</button>
      </div>
      
      <ul>
        {filteredTodos.map(todo => (
          <li 
            key={todo.id}
            onClick={() => handleToggle(todo.id)}
            style={{ 
              textDecoration: todo.completed ? 'line-through' : 'none' 
            }}
          >
            {todo.text}
            <button onClick={(e) => {
              e.stopPropagation();
              dispatch(deleteTodo(todo.id));
            }}>
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

// LoginForm.js
import { useDispatch, useSelector } from 'react-redux';
import { loginUser } from './userSlice';

function LoginForm() {
  const dispatch = useDispatch();
  const { loading, error } = useSelector(state => state.user);
  const [credentials, setCredentials] = useState({ email: '', password: '' });
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    await dispatch(loginUser(credentials));
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input 
        value={credentials.email}
        onChange={(e) => setCredentials({ ...credentials, email: e.target.value })}
      />
      <input 
        type="password"
        value={credentials.password}
        onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
      />
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
      {error && <div>{error}</div>}
    </form>
  );
}
```

### Redux Selectors

```javascript
// selectors.js
import { createSelector } from '@reduxjs/toolkit';

// Basic selector
export const selectTodos = state => state.todos.items;
export const selectFilter = state => state.todos.filter;

// Memoized selector
export const selectFilteredTodos = createSelector(
  [selectTodos, selectFilter],
  (todos, filter) => {
    switch (filter) {
      case 'active':
        return todos.filter(t => !t.completed);
      case 'completed':
        return todos.filter(t => t.completed);
      default:
        return todos;
    }
  }
);

export const selectTodoStats = createSelector(
  [selectTodos],
  (todos) => ({
    total: todos.length,
    completed: todos.filter(t => t.completed).length,
    active: todos.filter(t => !t.completed).length
  })
);

// Usage
function TodoStats() {
  const stats = useSelector(selectTodoStats);
  
  return (
    <div>
      <p>Total: {stats.total}</p>
      <p>Completed: {stats.completed}</p>
      <p>Active: {stats.active}</p>
    </div>
  );
}
```

## Zustand

Zustand is a small, fast, and scalable state management solution.

### Installation

```bash
npm install zustand
```

### Basic Store

```javascript
// store.js
import { create } from 'zustand';

export const useStore = create((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
  reset: () => set({ count: 0 })
}));

// Usage
function Counter() {
  const count = useStore(state => state.count);
  const increment = useStore(state => state.increment);
  const decrement = useStore(state => state.decrement);
  
  return (
    <div>
      <p>{count}</p>
      <button onClick={increment}>+</button>
      <button onClick={decrement}>-</button>
    </div>
  );
}
```

### Advanced Store with Async Actions

```javascript
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export const useTodoStore = create(
  devtools(
    persist(
      (set, get) => ({
        todos: [],
        filter: 'all',
        loading: false,
        error: null,
        
        // Actions
        addTodo: (text) => set((state) => ({
          todos: [...state.todos, {
            id: Date.now(),
            text,
            completed: false
          }]
        })),
        
        toggleTodo: (id) => set((state) => ({
          todos: state.todos.map(todo =>
            todo.id === id 
              ? { ...todo, completed: !todo.completed }
              : todo
          )
        })),
        
        deleteTodo: (id) => set((state) => ({
          todos: state.todos.filter(todo => todo.id !== id)
        })),
        
        setFilter: (filter) => set({ filter }),
        
        // Async action
        fetchTodos: async () => {
          set({ loading: true, error: null });
          
          try {
            const response = await fetch('/api/todos');
            const data = await response.json();
            set({ todos: data, loading: false });
          } catch (error) {
            set({ error: error.message, loading: false });
          }
        },
        
        // Computed values
        get filteredTodos() {
          const { todos, filter } = get();
          
          switch (filter) {
            case 'active':
              return todos.filter(t => !t.completed);
            case 'completed':
              return todos.filter(t => t.completed);
            default:
              return todos;
          }
        }
      }),
      {
        name: 'todo-storage', // localStorage key
        partialize: (state) => ({ todos: state.todos }) // Only persist todos
      }
    )
  )
);

// Usage
function TodoList() {
  const { 
    filteredTodos, 
    addTodo, 
    toggleTodo, 
    deleteTodo,
    setFilter,
    fetchTodos
  } = useTodoStore();
  
  useEffect(() => {
    fetchTodos();
  }, []);
  
  return (
    <div>
      <input onKeyPress={(e) => {
        if (e.key === 'Enter') {
          addTodo(e.target.value);
          e.target.value = '';
        }
      }} />
      
      <div>
        <button onClick={() => setFilter('all')}>All</button>
        <button onClick={() => setFilter('active')}>Active</button>
        <button onClick={() => setFilter('completed')}>Completed</button>
      </div>
      
      {filteredTodos.map(todo => (
        <div key={todo.id} onClick={() => toggleTodo(todo.id)}>
          {todo.text}
          <button onClick={(e) => {
            e.stopPropagation();
            deleteTodo(todo.id);
          }}>Delete</button>
        </div>
      ))}
    </div>
  );
}
```

### Slices Pattern

```javascript
// userSlice.js
export const createUserSlice = (set, get) => ({
  user: null,
  login: async (credentials) => {
    const response = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
    const user = await response.json();
    set({ user });
  },
  logout: () => set({ user: null })
});

// todosSlice.js
export const createTodosSlice = (set, get) => ({
  todos: [],
  addTodo: (text) => set((state) => ({
    todos: [...state.todos, { id: Date.now(), text, completed: false }]
  }))
});

// store.js
import { create } from 'zustand';
import { createUserSlice } from './userSlice';
import { createTodosSlice } from './todosSlice';

export const useStore = create((...args) => ({
  ...createUserSlice(...args),
  ...createTodosSlice(...args)
}));
```

## Comparing Solutions

### When to Use Each Solution

**Local State (`useState`):**
- Simple component state
- No state sharing needed
- UI state (toggles, form inputs)

**Context API:**
- Theme, locale, auth
- Moderate complexity
- Infrequent updates
- Small to medium apps

**Redux:**
- Large applications
- Complex state logic
- Time-travel debugging needed
- Team prefers strict patterns
- Heavy state interactions

**Zustand:**
- Medium to large apps
- Need simplicity + power
- Less boilerplate than Redux
- Modern, hooks-first approach

### Performance Comparison

```jsx
// Context - all consumers re-render when any value changes
const AppContext = createContext();

function App() {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('light');
  
  // Both values in one context - not optimal
  return (
    <AppContext.Provider value={{ user, setUser, theme, setTheme }}>
      <Component />
    </AppContext.Provider>
  );
}

// Redux - only affected components re-render
function Component() {
  const user = useSelector(state => state.user); // Only re-renders if user changes
  const theme = useSelector(state => state.theme); // Only re-renders if theme changes
}

// Zustand - granular subscriptions
function Component() {
  const user = useStore(state => state.user); // Only re-renders if user changes
  const theme = useStore(state => state.theme); // Only re-renders if theme changes
}
```

## Best Practices

### 1. Keep State Normalized

```javascript
// Bad - nested/denormalized
const state = {
  posts: [
    {
      id: 1,
      title: 'Post 1',
      author: {
        id: 1,
        name: 'John',
        email: 'john@example.com'
      },
      comments: [
        { id: 1, text: 'Comment 1', author: { id: 2, name: 'Jane' } }
      ]
    }
  ]
};

// Good - normalized
const state = {
  posts: {
    byId: {
      1: { id: 1, title: 'Post 1', authorId: 1, commentIds: [1] }
    },
    allIds: [1]
  },
  users: {
    byId: {
      1: { id: 1, name: 'John', email: 'john@example.com' },
      2: { id: 2, name: 'Jane', email: 'jane@example.com' }
    },
    allIds: [1, 2]
  },
  comments: {
    byId: {
      1: { id: 1, text: 'Comment 1', authorId: 2 }
    },
    allIds: [1]
  }
};
```

### 2. Separate Server State from UI State

```javascript
// Use React Query or SWR for server state
import { useQuery, useMutation } from '@tanstack/react-query';

function UserProfile({ userId }) {
  // Server state
  const { data: user, isLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetch(`/api/users/${userId}`).then(r => r.json())
  });
  
  // UI state
  const [isEditing, setIsEditing] = useState(false);
  
  return <div>{/* Render */}</div>;
}
```

### 3. Use Selectors for Derived State

```javascript
// Bad - deriving state in component
function TodoList() {
  const todos = useSelector(state => state.todos);
  const completedCount = todos.filter(t => t.completed).length; // Recalculates every render
  
  return <div>{completedCount} completed</div>;
}

// Good - memoized selector
const selectCompletedCount = createSelector(
  state => state.todos,
  todos => todos.filter(t => t.completed).length
);

function TodoList() {
  const completedCount = useSelector(selectCompletedCount); // Only recalculates when todos change
  
  return <div>{completedCount} completed</div>;
}
```

### 4. Avoid Unnecessary Global State

```jsx
// Bad - everything in global state
const store = create((set) => ({
  modalOpen: false, // This is local UI state!
  currentPage: 1, // This is local to pagination component!
  user: null // This should be global
}));

// Good - only truly global state
const store = create((set) => ({
  user: null,
  settings: {}
}));

// Local state in components
function Modal() {
  const [isOpen, setIsOpen] = useState(false); // Local state
  return <div>{/* ... */}</div>;
}
```

### 5. Colocate State

```jsx
// Bad - state too high in tree
function App() {
  const [formData, setFormData] = useState({}); // Only used in Form
  
  return (
    <div>
      <Header />
      <Sidebar />
      <Form data={formData} setData={setFormData} />
    </div>
  );
}

// Good - state in component that uses it
function App() {
  return (
    <div>
      <Header />
      <Sidebar />
      <Form />
    </div>
  );
}

function Form() {
  const [formData, setFormData] = useState({}); // Colocated
  return <div>{/* ... */}</div>;
}
```

### 6. Optimize Context Performance

```jsx
// Bad - single context causes unnecessary re-renders
const AppContext = createContext();

function Provider({ children }) {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('light');
  
  return (
    <AppContext.Provider value={{ user, setUser, theme, setTheme }}>
      {children}
    </AppContext.Provider>
  );
}

// Good - split contexts
const UserContext = createContext();
const ThemeContext = createContext();

function Provider({ children }) {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('light');
  
  return (
    <UserContext.Provider value={{ user, setUser }}>
      <ThemeContext.Provider value={{ theme, setTheme }}>
        {children}
      </ThemeContext.Provider>
    </UserContext.Provider>
  );
}
```

### 7. Handle Loading and Error States

```javascript
// Redux Toolkit
const userSlice = createSlice({
  name: 'user',
  initialState: {
    data: null,
    loading: false,
    error: null
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUser.fulfilled, (state, action) => {
        state.loading = false;
        state.data = action.payload;
      })
      .addCase(fetchUser.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  }
});

// Zustand
const useStore = create((set) => ({
  user: null,
  loading: false,
  error: null,
  
  fetchUser: async (id) => {
    set({ loading: true, error: null });
    
    try {
      const response = await fetch(`/api/users/${id}`);
      const data = await response.json();
      set({ user: data, loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
    }
  }
}));
```

### 8. TypeScript Support

```typescript
// Redux Toolkit with TypeScript
import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';

export const store = configureStore({
  reducer: {
    todos: todosReducer,
    user: userReducer
  }
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Typed hooks
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// Usage
function Component() {
  const todos = useAppSelector(state => state.todos); // Fully typed
  const dispatch = useAppDispatch(); // Fully typed
}

// Zustand with TypeScript
interface TodoState {
  todos: Todo[];
  addTodo: (text: string) => void;
  toggleTodo: (id: number) => void;
}

export const useTodoStore = create<TodoState>((set) => ({
  todos: [],
  addTodo: (text) => set((state) => ({
    todos: [...state.todos, { id: Date.now(), text, completed: false }]
  })),
  toggleTodo: (id) => set((state) => ({
    todos: state.todos.map(t => 
      t.id === id ? { ...t, completed: !t.completed } : t
    )
  }))
}));
```
