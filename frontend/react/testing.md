# React Testing Guidelines

## Table of Contents
- [Overview](#overview)
- [Testing Setup](#testing-setup)
- [Testing Library Basics](#testing-library-basics)
- [Component Testing](#component-testing)
- [Testing Hooks](#testing-hooks)
- [Testing Async Operations](#testing-async-operations)
- [Mocking](#mocking)
- [Integration Testing](#integration-testing)
- [Coverage](#coverage)
- [Best Practices](#best-practices)

## Overview

Testing React applications ensures reliability, maintainability, and confidence in code changes. Modern React testing emphasizes user-centric testing with React Testing Library and Jest.

## Testing Setup

### Installation

```bash
# Core testing dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event

# Jest (usually included with Create React App)
npm install --save-dev jest jest-environment-jsdom

# For testing hooks
npm install --save-dev @testing-library/react-hooks
```

### Jest Configuration

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '\\.(jpg|jpeg|png|gif|svg)$': '<rootDir>/__mocks__/fileMock.js'
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.js',
    '!src/reportWebVitals.js'
  ],
  coverageThresholds: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  }
};
```

### Setup File

```javascript
// src/setupTests.js
import '@testing-library/jest-dom';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() { return []; }
  unobserve() {}
};
```

## Testing Library Basics

### Basic Test Structure

```jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Button from './Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('calls onClick when clicked', async () => {
    const handleClick = jest.fn();
    const user = userEvent.setup();
    
    render(<Button onClick={handleClick}>Click me</Button>);
    
    await user.click(screen.getByText('Click me'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### Query Methods

```jsx
import { render, screen } from '@testing-library/react';

function UserProfile({ user }) {
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
      <img src={user.avatar} alt={user.name} />
    </div>
  );
}

test('query methods', () => {
  const user = {
    name: 'John Doe',
    email: 'john@example.com',
    avatar: 'avatar.jpg'
  };
  
  render(<UserProfile user={user} />);
  
  // getBy - throws error if not found
  expect(screen.getByText('John Doe')).toBeInTheDocument();
  
  // queryBy - returns null if not found
  expect(screen.queryByText('Not here')).not.toBeInTheDocument();
  
  // findBy - async, waits for element
  const heading = await screen.findByRole('heading');
  expect(heading).toHaveTextContent('John Doe');
  
  // getAllBy - returns array
  const paragraphs = screen.getAllByRole('paragraph');
  expect(paragraphs).toHaveLength(1);
  
  // getByRole - preferred for accessibility
  expect(screen.getByRole('heading', { name: 'John Doe' })).toBeInTheDocument();
  expect(screen.getByRole('img', { name: 'John Doe' })).toBeInTheDocument();
  
  // getByLabelText - for form inputs
  // getByPlaceholderText - by placeholder
  // getByAltText - for images
  // getByTitle - by title attribute
  // getByTestId - by data-testid (use sparingly)
});
```

### User Events

```jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

function LoginForm({ onSubmit }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({ email, password });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="email">Email</label>
      <input 
        id="email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      
      <label htmlFor="password">Password</label>
      <input 
        id="password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      
      <button type="submit">Login</button>
    </form>
  );
}

describe('LoginForm', () => {
  it('submits form with user input', async () => {
    const handleSubmit = jest.fn();
    const user = userEvent.setup();
    
    render(<LoginForm onSubmit={handleSubmit} />);
    
    // Type in inputs
    await user.type(
      screen.getByLabelText('Email'),
      'john@example.com'
    );
    await user.type(
      screen.getByLabelText('Password'),
      'password123'
    );
    
    // Click button
    await user.click(screen.getByRole('button', { name: 'Login' }));
    
    expect(handleSubmit).toHaveBeenCalledWith({
      email: 'john@example.com',
      password: 'password123'
    });
  });
  
  it('handles keyboard interactions', async () => {
    const user = userEvent.setup();
    
    render(<LoginForm onSubmit={jest.fn()} />);
    
    const emailInput = screen.getByLabelText('Email');
    
    // Tab to input
    await user.tab();
    expect(emailInput).toHaveFocus();
    
    // Type and clear
    await user.type(emailInput, 'test@example.com');
    await user.clear(emailInput);
    expect(emailInput).toHaveValue('');
    
    // Paste
    await user.paste('pasted@example.com');
    expect(emailInput).toHaveValue('pasted@example.com');
  });
});
```

## Component Testing

### Testing Props

```jsx
function Greeting({ name, age, onGreet }) {
  return (
    <div>
      <h1>Hello, {name}!</h1>
      <p>Age: {age}</p>
      <button onClick={onGreet}>Greet</button>
    </div>
  );
}

describe('Greeting', () => {
  it('displays user information', () => {
    render(<Greeting name="John" age={30} onGreet={jest.fn()} />);
    
    expect(screen.getByText('Hello, John!')).toBeInTheDocument();
    expect(screen.getByText('Age: 30')).toBeInTheDocument();
  });
  
  it('calls onGreet when button clicked', async () => {
    const handleGreet = jest.fn();
    const user = userEvent.setup();
    
    render(<Greeting name="John" age={30} onGreet={handleGreet} />);
    
    await user.click(screen.getByRole('button', { name: 'Greet' }));
    
    expect(handleGreet).toHaveBeenCalled();
  });
});
```

### Testing State Changes

```jsx
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

describe('Counter', () => {
  it('increments count', async () => {
    const user = userEvent.setup();
    
    render(<Counter />);
    
    expect(screen.getByText('Count: 0')).toBeInTheDocument();
    
    await user.click(screen.getByRole('button', { name: 'Increment' }));
    expect(screen.getByText('Count: 1')).toBeInTheDocument();
    
    await user.click(screen.getByRole('button', { name: 'Increment' }));
    expect(screen.getByText('Count: 2')).toBeInTheDocument();
  });
  
  it('decrements count', async () => {
    const user = userEvent.setup();
    
    render(<Counter />);
    
    await user.click(screen.getByRole('button', { name: 'Decrement' }));
    expect(screen.getByText('Count: -1')).toBeInTheDocument();
  });
  
  it('resets count', async () => {
    const user = userEvent.setup();
    
    render(<Counter />);
    
    await user.click(screen.getByRole('button', { name: 'Increment' }));
    await user.click(screen.getByRole('button', { name: 'Increment' }));
    await user.click(screen.getByRole('button', { name: 'Reset' }));
    
    expect(screen.getByText('Count: 0')).toBeInTheDocument();
  });
});
```

### Testing Conditional Rendering

```jsx
function Message({ type, text }) {
  if (!text) return null;
  
  return (
    <div className={`message message-${type}`}>
      {type === 'error' && <span role="img" aria-label="error">❌</span>}
      {type === 'success' && <span role="img" aria-label="success">✅</span>}
      {text}
    </div>
  );
}

describe('Message', () => {
  it('renders nothing when no text', () => {
    const { container } = render(<Message type="info" text="" />);
    
    expect(container).toBeEmptyDOMElement();
  });
  
  it('renders error message', () => {
    render(<Message type="error" text="Error occurred" />);
    
    expect(screen.getByText('Error occurred')).toBeInTheDocument();
    expect(screen.getByLabelText('error')).toBeInTheDocument();
  });
  
  it('renders success message', () => {
    render(<Message type="success" text="Success!" />);
    
    expect(screen.getByText('Success!')).toBeInTheDocument();
    expect(screen.getByLabelText('success')).toBeInTheDocument();
  });
});
```

### Testing Lists

```jsx
function TodoList({ todos, onToggle, onDelete }) {
  return (
    <ul>
      {todos.map(todo => (
        <li key={todo.id}>
          <input
            type="checkbox"
            checked={todo.completed}
            onChange={() => onToggle(todo.id)}
            aria-label={`Toggle ${todo.text}`}
          />
          <span style={{ 
            textDecoration: todo.completed ? 'line-through' : 'none' 
          }}>
            {todo.text}
          </span>
          <button onClick={() => onDelete(todo.id)}>Delete</button>
        </li>
      ))}
    </ul>
  );
}

describe('TodoList', () => {
  const mockTodos = [
    { id: 1, text: 'Buy milk', completed: false },
    { id: 2, text: 'Walk dog', completed: true },
    { id: 3, text: 'Write code', completed: false }
  ];
  
  it('renders all todos', () => {
    render(
      <TodoList 
        todos={mockTodos}
        onToggle={jest.fn()}
        onDelete={jest.fn()}
      />
    );
    
    expect(screen.getByText('Buy milk')).toBeInTheDocument();
    expect(screen.getByText('Walk dog')).toBeInTheDocument();
    expect(screen.getByText('Write code')).toBeInTheDocument();
  });
  
  it('calls onToggle when checkbox clicked', async () => {
    const handleToggle = jest.fn();
    const user = userEvent.setup();
    
    render(
      <TodoList 
        todos={mockTodos}
        onToggle={handleToggle}
        onDelete={jest.fn()}
      />
    );
    
    await user.click(screen.getByLabelText('Toggle Buy milk'));
    
    expect(handleToggle).toHaveBeenCalledWith(1);
  });
  
  it('calls onDelete when delete clicked', async () => {
    const handleDelete = jest.fn();
    const user = userEvent.setup();
    
    render(
      <TodoList 
        todos={mockTodos}
        onToggle={jest.fn()}
        onDelete={handleDelete}
      />
    );
    
    const deleteButtons = screen.getAllByRole('button', { name: 'Delete' });
    await user.click(deleteButtons[0]);
    
    expect(handleDelete).toHaveBeenCalledWith(1);
  });
});
```

## Testing Hooks

### Testing Custom Hooks

```jsx
import { renderHook, act } from '@testing-library/react';

function useCounter(initialValue = 0) {
  const [count, setCount] = useState(initialValue);
  
  const increment = () => setCount(c => c + 1);
  const decrement = () => setCount(c => c - 1);
  const reset = () => setCount(initialValue);
  
  return { count, increment, decrement, reset };
}

describe('useCounter', () => {
  it('initializes with default value', () => {
    const { result } = renderHook(() => useCounter());
    
    expect(result.current.count).toBe(0);
  });
  
  it('initializes with custom value', () => {
    const { result } = renderHook(() => useCounter(10));
    
    expect(result.current.count).toBe(10);
  });
  
  it('increments count', () => {
    const { result } = renderHook(() => useCounter());
    
    act(() => {
      result.current.increment();
    });
    
    expect(result.current.count).toBe(1);
  });
  
  it('decrements count', () => {
    const { result } = renderHook(() => useCounter(5));
    
    act(() => {
      result.current.decrement();
    });
    
    expect(result.current.count).toBe(4);
  });
  
  it('resets to initial value', () => {
    const { result } = renderHook(() => useCounter(10));
    
    act(() => {
      result.current.increment();
      result.current.increment();
      result.current.reset();
    });
    
    expect(result.current.count).toBe(10);
  });
});
```

### Testing Hooks with Dependencies

```jsx
function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);
    
    return () => clearTimeout(timer);
  }, [value, delay]);
  
  return debouncedValue;
}

describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });
  
  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });
  
  it('debounces value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 500 } }
    );
    
    expect(result.current).toBe('initial');
    
    // Update value
    rerender({ value: 'updated', delay: 500 });
    
    // Value not updated yet
    expect(result.current).toBe('initial');
    
    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(500);
    });
    
    // Value updated
    expect(result.current).toBe('updated');
  });
});
```

## Testing Async Operations

### Testing Data Fetching

```jsx
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(res => res.json())
      .then(data => {
        setUser(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [userId]);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
}

describe('UserProfile', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });
  
  afterEach(() => {
    jest.restoreAllMocks();
  });
  
  it('displays loading state', () => {
    fetch.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<UserProfile userId="123" />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });
  
  it('displays user data when loaded', async () => {
    const mockUser = {
      name: 'John Doe',
      email: 'john@example.com'
    };
    
    fetch.mockResolvedValueOnce({
      json: async () => mockUser
    });
    
    render(<UserProfile userId="123" />);
    
    // Wait for loading to complete
    expect(await screen.findByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });
  
  it('displays error when fetch fails', async () => {
    fetch.mockRejectedValueOnce(new Error('Failed to fetch'));
    
    render(<UserProfile userId="123" />);
    
    expect(await screen.findByText(/Error: Failed to fetch/)).toBeInTheDocument();
  });
});
```

### Testing with waitFor

```jsx
import { render, screen, waitFor } from '@testing-library/react';

function SearchResults({ query }) {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (!query) {
      setResults([]);
      return;
    }
    
    setLoading(true);
    
    fetch(`/api/search?q=${query}`)
      .then(res => res.json())
      .then(data => {
        setResults(data);
        setLoading(false);
      });
  }, [query]);
  
  if (loading) return <div>Searching...</div>;
  
  return (
    <ul>
      {results.map(result => (
        <li key={result.id}>{result.title}</li>
      ))}
    </ul>
  );
}

describe('SearchResults', () => {
  it('fetches and displays results', async () => {
    const mockResults = [
      { id: 1, title: 'Result 1' },
      { id: 2, title: 'Result 2' }
    ];
    
    global.fetch = jest.fn().mockResolvedValue({
      json: async () => mockResults
    });
    
    const { rerender } = render(<SearchResults query="" />);
    
    // Update query
    rerender(<SearchResults query="react" />);
    
    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText('Result 1')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Result 2')).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith('/api/search?q=react');
  });
});
```

## Mocking

### Mocking Modules

```javascript
// api.js
export async function fetchUser(id) {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}

// Component.jsx
import { fetchUser } from './api';

function UserDisplay({ userId }) {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);
  
  return user ? <div>{user.name}</div> : null;
}

// Component.test.jsx
import { fetchUser } from './api';

jest.mock('./api');

describe('UserDisplay', () => {
  it('displays user name', async () => {
    fetchUser.mockResolvedValue({ name: 'John Doe' });
    
    render(<UserDisplay userId="123" />);
    
    expect(await screen.findByText('John Doe')).toBeInTheDocument();
    expect(fetchUser).toHaveBeenCalledWith('123');
  });
});
```

### Mocking Context

```jsx
// authContext.js
const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  return (
    <AuthContext.Provider value={{ user, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

// Component.jsx
function UserGreeting() {
  const { user } = useAuth();
  
  if (!user) return <div>Please login</div>;
  
  return <div>Hello, {user.name}</div>;
}

// Component.test.jsx
function renderWithAuth(component, { user = null } = {}) {
  return render(
    <AuthContext.Provider value={{ user, setUser: jest.fn() }}>
      {component}
    </AuthContext.Provider>
  );
}

describe('UserGreeting', () => {
  it('shows login message when no user', () => {
    renderWithAuth(<UserGreeting />);
    
    expect(screen.getByText('Please login')).toBeInTheDocument();
  });
  
  it('shows greeting when user exists', () => {
    const mockUser = { name: 'John' };
    
    renderWithAuth(<UserGreeting />, { user: mockUser });
    
    expect(screen.getByText('Hello, John')).toBeInTheDocument();
  });
});
```

### Mocking React Router

```jsx
import { MemoryRouter, Route, Routes } from 'react-router-dom';

function renderWithRouter(component, { route = '/' } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route path="*" element={component} />
      </Routes>
    </MemoryRouter>
  );
}

describe('UserProfile', () => {
  it('displays user based on route param', () => {
    renderWithRouter(<UserProfile />, { route: '/users/123' });
    
    // Test component with userId param
  });
});
```

### Mocking Timers

```jsx
function DelayedMessage({ message, delay }) {
  const [show, setShow] = useState(false);
  
  useEffect(() => {
    const timer = setTimeout(() => setShow(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);
  
  return show ? <div>{message}</div> : null;
}

describe('DelayedMessage', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });
  
  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });
  
  it('shows message after delay', () => {
    render(<DelayedMessage message="Hello" delay={1000} />);
    
    expect(screen.queryByText('Hello')).not.toBeInTheDocument();
    
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

## Integration Testing

### Testing Component Integration

```jsx
function TodoApp() {
  const [todos, setTodos] = useState([]);
  const [input, setInput] = useState('');
  
  const addTodo = () => {
    if (input.trim()) {
      setTodos([...todos, { id: Date.now(), text: input, completed: false }]);
      setInput('');
    }
  };
  
  const toggleTodo = (id) => {
    setTodos(todos.map(t => 
      t.id === id ? { ...t, completed: !t.completed } : t
    ));
  };
  
  return (
    <div>
      <input 
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Add todo"
      />
      <button onClick={addTodo}>Add</button>
      
      <ul>
        {todos.map(todo => (
          <li key={todo.id}>
            <input
              type="checkbox"
              checked={todo.completed}
              onChange={() => toggleTodo(todo.id)}
            />
            <span>{todo.text}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

describe('TodoApp Integration', () => {
  it('adds and toggles todos', async () => {
    const user = userEvent.setup();
    
    render(<TodoApp />);
    
    // Add first todo
    await user.type(screen.getByPlaceholderText('Add todo'), 'Buy milk');
    await user.click(screen.getByRole('button', { name: 'Add' }));
    
    expect(screen.getByText('Buy milk')).toBeInTheDocument();
    
    // Add second todo
    await user.type(screen.getByPlaceholderText('Add todo'), 'Walk dog');
    await user.click(screen.getByRole('button', { name: 'Add' }));
    
    expect(screen.getByText('Walk dog')).toBeInTheDocument();
    
    // Toggle first todo
    const checkboxes = screen.getAllByRole('checkbox');
    await user.click(checkboxes[0]);
    
    expect(checkboxes[0]).toBeChecked();
    expect(checkboxes[1]).not.toBeChecked();
  });
});
```

## Coverage

### Running Coverage

```bash
# Run tests with coverage
npm test -- --coverage

# Run coverage for specific files
npm test -- --coverage --collectCoverageFrom="src/components/**/*.{js,jsx}"

# Watch mode with coverage
npm test -- --coverage --watchAll
```

### Coverage Configuration

```javascript
// jest.config.js
module.exports = {
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.js',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/*.test.{js,jsx,ts,tsx}'
  ],
  coverageThresholds: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './src/components/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    }
  },
  coverageReporters: ['text', 'lcov', 'html']
};
```

## Best Practices

### 1. Test User Behavior, Not Implementation

```jsx
// Bad - testing implementation details
it('updates state when input changes', () => {
  const { result } = renderHook(() => useState(''));
  
  act(() => {
    result.current[1]('new value');
  });
  
  expect(result.current[0]).toBe('new value');
});

// Good - testing user behavior
it('updates input value when user types', async () => {
  const user = userEvent.setup();
  
  render(<SearchInput />);
  
  await user.type(screen.getByRole('textbox'), 'search query');
  
  expect(screen.getByRole('textbox')).toHaveValue('search query');
});
```

### 2. Use Accessible Queries

```jsx
// Bad - fragile queries
screen.getByTestId('submit-button');
screen.getByClassName('user-name');

// Good - accessible queries
screen.getByRole('button', { name: 'Submit' });
screen.getByLabelText('Username');
screen.getByText('John Doe');
```

### 3. Avoid Testing Third-Party Libraries

```jsx
// Bad - testing React Router
it('navigates to home', () => {
  // Don't test that Link works
  expect(screen.getByRole('link')).toHaveAttribute('href', '/');
});

// Good - test your component's behavior
it('displays navigation links', () => {
  render(<Navigation />);
  
  expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'About' })).toBeInTheDocument();
});
```

### 4. Keep Tests Isolated

```jsx
// Bad - tests depend on each other
describe('Counter', () => {
  let result;
  
  it('initializes at 0', () => {
    result = renderHook(() => useCounter());
    expect(result.current.count).toBe(0);
  });
  
  it('increments', () => {
    act(() => result.current.increment()); // Depends on previous test
    expect(result.current.count).toBe(1);
  });
});

// Good - independent tests
describe('Counter', () => {
  it('initializes at 0', () => {
    const { result } = renderHook(() => useCounter());
    expect(result.current.count).toBe(0);
  });
  
  it('increments from initial value', () => {
    const { result } = renderHook(() => useCounter());
    
    act(() => result.current.increment());
    
    expect(result.current.count).toBe(1);
  });
});
```

### 5. Use Custom Render Functions

```jsx
// test-utils.jsx
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from './ThemeContext';

function AllTheProviders({ children }) {
  return (
    <BrowserRouter>
      <ThemeProvider>
        {children}
      </ThemeProvider>
    </BrowserRouter>
  );
}

const customRender = (ui, options) =>
  render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };

// Component.test.jsx
import { render, screen } from './test-utils';

test('component with providers', () => {
  render(<MyComponent />);
  // Component has access to all providers
});
```

### 6. Test Error States

```jsx
describe('UserProfile', () => {
  it('handles network errors gracefully', async () => {
    global.fetch = jest.fn().mockRejectedValue(
      new Error('Network error')
    );
    
    render(<UserProfile userId="123" />);
    
    expect(
      await screen.findByText(/Network error/)
    ).toBeInTheDocument();
  });
  
  it('handles 404 errors', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: async () => ({ error: 'User not found' })
    });
    
    render(<UserProfile userId="999" />);
    
    expect(
      await screen.findByText(/User not found/)
    ).toBeInTheDocument();
  });
});
```

### 7. Organize Tests with describe Blocks

```jsx
describe('UserProfile', () => {
  describe('when loading', () => {
    it('shows loading spinner', () => {
      // Test loading state
    });
  });
  
  describe('when loaded successfully', () => {
    it('displays user information', () => {
      // Test success state
    });
    
    it('allows editing profile', () => {
      // Test interaction
    });
  });
  
  describe('when error occurs', () => {
    it('displays error message', () => {
      // Test error state
    });
    
    it('provides retry option', () => {
      // Test error recovery
    });
  });
});
```

### 8. Snapshot Testing (Use Sparingly)

```jsx
import { render } from '@testing-library/react';

it('matches snapshot', () => {
  const { container } = render(<Button variant="primary">Click me</Button>);
  
  expect(container.firstChild).toMatchSnapshot();
});

// Update snapshots when intentional changes made:
// npm test -- -u
```
