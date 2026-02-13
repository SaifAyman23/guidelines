# React Project Structure Guidelines

## Table of Contents
- [Overview](#overview)
- [Folder Organization](#folder-organization)
- [File Naming Conventions](#file-naming-conventions)
- [Feature-Based Structure](#feature-based-structure)
- [Layer-Based Structure](#layer-based-structure)
- [Module Structure](#module-structure)
- [Scalability Patterns](#scalability-patterns)
- [Best Practices](#best-practices)

## Overview

A well-organized project structure improves code maintainability, scalability, and team collaboration. Choose a structure that fits your team size and project complexity.

## Folder Organization

### Small Project Structure

```
src/
├── components/
│   ├── Button.jsx
│   ├── Card.jsx
│   ├── Input.jsx
│   └── Modal.jsx
├── pages/
│   ├── Home.jsx
│   ├── About.jsx
│   └── Contact.jsx
├── hooks/
│   ├── useAuth.js
│   └── useFetch.js
├── utils/
│   ├── api.js
│   └── helpers.js
├── App.jsx
├── index.jsx
└── index.css
```

### Medium Project Structure

```
src/
├── assets/
│   ├── images/
│   ├── icons/
│   └── fonts/
├── components/
│   ├── common/
│   │   ├── Button/
│   │   ├── Input/
│   │   └── Modal/
│   ├── layout/
│   │   ├── Header/
│   │   ├── Footer/
│   │   └── Sidebar/
│   └── features/
│       ├── UserProfile/
│       └── ProductCard/
├── pages/
│   ├── Home/
│   ├── Dashboard/
│   └── Settings/
├── hooks/
│   ├── useAuth.js
│   ├── useFetch.js
│   └── useLocalStorage.js
├── context/
│   ├── AuthContext.jsx
│   └── ThemeContext.jsx
├── services/
│   ├── api.js
│   ├── auth.js
│   └── storage.js
├── utils/
│   ├── helpers.js
│   ├── validators.js
│   └── constants.js
├── styles/
│   ├── globals.css
│   └── variables.css
├── App.jsx
└── index.jsx
```

### Large Project Structure

```
src/
├── app/
│   ├── App.jsx
│   ├── App.test.jsx
│   ├── routes.jsx
│   └── store.js
├── features/
│   ├── auth/
│   │   ├── components/
│   │   │   ├── LoginForm/
│   │   │   └── RegisterForm/
│   │   ├── hooks/
│   │   │   └── useAuth.js
│   │   ├── services/
│   │   │   └── authService.js
│   │   ├── slices/
│   │   │   └── authSlice.js
│   │   └── index.js
│   ├── products/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── slices/
│   │   └── index.js
│   └── users/
│       ├── components/
│       ├── hooks/
│       ├── services/
│       ├── slices/
│       └── index.js
├── shared/
│   ├── components/
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Modal/
│   │   └── Table/
│   ├── hooks/
│   │   ├── useDebounce.js
│   │   ├── useLocalStorage.js
│   │   └── useMediaQuery.js
│   ├── utils/
│   │   ├── api.js
│   │   ├── validators.js
│   │   └── formatters.js
│   ├── constants/
│   │   ├── routes.js
│   │   └── config.js
│   └── types/
│       └── index.ts
├── layouts/
│   ├── MainLayout/
│   ├── AuthLayout/
│   └── DashboardLayout/
├── pages/
│   ├── Home/
│   ├── Dashboard/
│   └── NotFound/
├── assets/
│   ├── images/
│   ├── icons/
│   └── fonts/
├── styles/
│   ├── globals.css
│   ├── variables.css
│   └── mixins.css
├── config/
│   ├── env.js
│   └── theme.js
├── lib/
│   └── axios.js
└── index.jsx
```

## File Naming Conventions

### Component Files

```
// PascalCase for components
Button.jsx
UserProfile.jsx
ProductCard.jsx

// Index pattern
Button/
├── Button.jsx
├── Button.test.jsx
├── Button.module.css
└── index.js
```

### Hook Files

```
// camelCase with 'use' prefix
useAuth.js
useFetch.js
useLocalStorage.js
useDebounce.js
```

### Utility Files

```
// camelCase for utilities
api.js
helpers.js
validators.js
formatters.js
constants.js
```

### Page Files

```
// PascalCase for pages
Home.jsx
Dashboard.jsx
UserProfile.jsx
NotFound.jsx
```

### Test Files

```
// Same name as file being tested + .test or .spec
Button.test.jsx
useAuth.test.js
api.spec.js
```

### Style Files

```
// CSS Modules
Button.module.css
UserProfile.module.css

// Regular CSS
globals.css
variables.css

// SCSS
Button.scss
_variables.scss
```

## Feature-Based Structure

Organize by feature/domain rather than file type. Each feature is self-contained.

### Feature Structure

```
features/
└── todos/
    ├── components/
    │   ├── TodoList/
    │   │   ├── TodoList.jsx
    │   │   ├── TodoList.test.jsx
    │   │   ├── TodoList.module.css
    │   │   └── index.js
    │   ├── TodoItem/
    │   └── TodoForm/
    ├── hooks/
    │   ├── useTodos.js
    │   └── useTodoFilters.js
    ├── services/
    │   └── todoService.js
    ├── slices/
    │   └── todoSlice.js
    ├── types/
    │   └── todo.types.ts
    ├── utils/
    │   └── todoHelpers.js
    ├── constants.js
    └── index.js
```

### Feature Example

```javascript
// features/todos/index.js
// Public API for the feature
export { TodoList } from './components/TodoList';
export { TodoForm } from './components/TodoForm';
export { useTodos } from './hooks/useTodos';
export { todoSlice } from './slices/todoSlice';

// features/todos/components/TodoList/TodoList.jsx
import React from 'react';
import { useTodos } from '../../hooks/useTodos';
import { TodoItem } from '../TodoItem';
import styles from './TodoList.module.css';

export function TodoList() {
  const { todos, loading, error } = useTodos();
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <ul className={styles.list}>
      {todos.map(todo => (
        <TodoItem key={todo.id} todo={todo} />
      ))}
    </ul>
  );
}

// features/todos/hooks/useTodos.js
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchTodos } from '../slices/todoSlice';

export function useTodos() {
  const dispatch = useDispatch();
  const { todos, loading, error } = useSelector(state => state.todos);
  
  useEffect(() => {
    dispatch(fetchTodos());
  }, [dispatch]);
  
  return { todos, loading, error };
}

// features/todos/services/todoService.js
import { api } from '@/shared/utils/api';

export const todoService = {
  getAll: () => api.get('/todos'),
  getById: (id) => api.get(`/todos/${id}`),
  create: (data) => api.post('/todos', data),
  update: (id, data) => api.put(`/todos/${id}`, data),
  delete: (id) => api.delete(`/todos/${id}`)
};
```

### Benefits of Feature-Based Structure

1. **Encapsulation**: Each feature is self-contained
2. **Scalability**: Easy to add new features
3. **Discoverability**: Related code is together
4. **Maintainability**: Changes stay within feature
5. **Testing**: Easy to test entire feature
6. **Team collaboration**: Teams can own features

## Layer-Based Structure

Organize by technical role/layer. Traditional MVC-style organization.

### Layer Structure

```
src/
├── components/
│   ├── common/
│   │   ├── Button/
│   │   ├── Input/
│   │   └── Modal/
│   ├── layout/
│   │   ├── Header/
│   │   ├── Footer/
│   │   └── Sidebar/
│   ├── todos/
│   │   ├── TodoList/
│   │   ├── TodoItem/
│   │   └── TodoForm/
│   └── users/
│       ├── UserList/
│       ├── UserCard/
│       └── UserProfile/
├── hooks/
│   ├── auth/
│   │   └── useAuth.js
│   ├── todos/
│   │   ├── useTodos.js
│   │   └── useTodoFilters.js
│   └── common/
│       ├── useDebounce.js
│       └── useLocalStorage.js
├── services/
│   ├── authService.js
│   ├── todoService.js
│   └── userService.js
├── store/
│   ├── slices/
│   │   ├── authSlice.js
│   │   ├── todoSlice.js
│   │   └── userSlice.js
│   └── store.js
├── pages/
│   ├── Home/
│   ├── Todos/
│   └── Profile/
├── utils/
│   ├── api.js
│   ├── validators.js
│   └── formatters.js
└── constants/
    ├── routes.js
    └── config.js
```

### Benefits of Layer-Based Structure

1. **Familiar**: Traditional MVC pattern
2. **Simple**: Easy to understand
3. **Type-focused**: Find all components easily
4. **Good for small apps**: Works well initially

### Drawbacks

1. **Scattered features**: Related code separated
2. **Hard to scale**: Gets messy with growth
3. **Difficult navigation**: Jump between folders
4. **Coupling**: Features can become intertwined

## Module Structure

### Component Module Template

```
Button/
├── Button.jsx            # Main component
├── Button.test.jsx       # Unit tests
├── Button.stories.jsx    # Storybook stories
├── Button.module.css     # Scoped styles
├── Button.types.ts       # TypeScript types
├── useButton.js          # Component-specific hook
└── index.js              # Public exports
```

### Complete Component Example

```jsx
// Button/Button.jsx
import React from 'react';
import PropTypes from 'prop-types';
import styles from './Button.module.css';

export function Button({ 
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  children,
  onClick,
  ...props
}) {
  const className = [
    styles.button,
    styles[variant],
    styles[size],
    loading && styles.loading,
    disabled && styles.disabled
  ].filter(Boolean).join(' ');
  
  return (
    <button
      className={className}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </button>
  );
}

Button.propTypes = {
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger']),
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  disabled: PropTypes.bool,
  loading: PropTypes.bool,
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func
};

// Button/Button.test.jsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('calls onClick when clicked', async () => {
    const handleClick = jest.fn();
    const user = userEvent.setup();
    
    render(<Button onClick={handleClick}>Click me</Button>);
    await user.click(screen.getByRole('button'));
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

// Button/index.js
export { Button } from './Button';
export { default } from './Button';
```

### Page Module Template

```
Dashboard/
├── Dashboard.jsx
├── Dashboard.test.jsx
├── Dashboard.module.css
├── components/
│   ├── DashboardHeader.jsx
│   ├── DashboardStats.jsx
│   └── DashboardChart.jsx
├── hooks/
│   └── useDashboardData.js
└── index.js
```

### Shared Utilities Structure

```
shared/
├── components/
│   ├── Button/
│   ├── Input/
│   └── Modal/
├── hooks/
│   ├── useDebounce.js
│   ├── useLocalStorage.js
│   └── useMediaQuery.js
├── utils/
│   ├── api/
│   │   ├── client.js
│   │   ├── endpoints.js
│   │   └── index.js
│   ├── validators/
│   │   ├── email.js
│   │   ├── phone.js
│   │   └── index.js
│   └── formatters/
│       ├── date.js
│       ├── currency.js
│       └── index.js
├── constants/
│   ├── routes.js
│   ├── config.js
│   └── messages.js
└── types/
    ├── user.types.ts
    └── api.types.ts
```

## Scalability Patterns

### Barrel Exports

Use index.js files to create clean public APIs.

```javascript
// components/index.js
export { Button } from './Button';
export { Input } from './Input';
export { Modal } from './Modal';
export { Table } from './Table';

// Usage
import { Button, Input, Modal } from '@/components';
```

### Path Aliases

Configure path aliases for cleaner imports.

```javascript
// jsconfig.json or tsconfig.json
{
  "compilerOptions": {
    "baseUrl": "src",
    "paths": {
      "@/*": ["*"],
      "@/components/*": ["components/*"],
      "@/features/*": ["features/*"],
      "@/shared/*": ["shared/*"],
      "@/hooks/*": ["hooks/*"],
      "@/utils/*": ["utils/*"]
    }
  }
}

// Before
import { Button } from '../../../shared/components/Button';

// After
import { Button } from '@/shared/components/Button';
```

### Dependency Boundaries

Establish clear import rules between layers.

```javascript
// ✅ Allowed imports
features/todos → shared/components
features/todos → shared/hooks
features/todos → shared/utils

// ❌ Not allowed
shared/components → features/todos
features/todos → features/users

// Configure with ESLint
// .eslintrc.js
module.exports = {
  rules: {
    'import/no-restricted-paths': ['error', {
      zones: [
        {
          target: './src/shared',
          from: './src/features',
          message: 'Shared modules should not import from features'
        },
        {
          target: './src/features/todos',
          from: './src/features/users',
          message: 'Features should not import from other features'
        }
      ]
    }]
  }
};
```

### Code Splitting by Route

```jsx
// app/routes.jsx
import { lazy } from 'react';

const Home = lazy(() => import('@/pages/Home'));
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Profile = lazy(() => import('@/pages/Profile'));

export const routes = [
  { path: '/', element: Home },
  { path: '/dashboard', element: Dashboard },
  { path: '/profile', element: Profile }
];

// app/App.jsx
import { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { routes } from './routes';

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        {routes.map(({ path, element: Element }) => (
          <Route key={path} path={path} element={<Element />} />
        ))}
      </Routes>
    </Suspense>
  );
}
```

## Best Practices

### 1. Consistent Naming

```
// Components: PascalCase
Button.jsx
UserProfile.jsx

// Hooks: camelCase with 'use' prefix
useAuth.js
useFetch.js

// Utils: camelCase
api.js
formatDate.js

// Constants: UPPER_SNAKE_CASE
const API_URL = 'https://api.example.com';
const MAX_RETRIES = 3;
```

### 2. Colocation

Keep related files together.

```
// Good
features/todos/
├── components/
├── hooks/
├── services/
└── slices/

// Bad
components/todos/
hooks/todos/
services/todos/
slices/todos/
```

### 3. Single Responsibility

Each file should have one clear purpose.

```javascript
// Good
// userService.js - only API calls
export const userService = {
  getAll: () => api.get('/users'),
  getById: (id) => api.get(`/users/${id}`)
};

// userHelpers.js - only helper functions
export function formatUserName(user) {
  return `${user.firstName} ${user.lastName}`;
}

// Bad - mixed responsibilities
export const userUtils = {
  getAll: () => api.get('/users'),
  formatName: (user) => `${user.firstName} ${user.lastName}`
};
```

### 4. Clear Public APIs

Use index.js to define what's public.

```javascript
// features/todos/index.js
// Public API
export { TodoList } from './components/TodoList';
export { useTodos } from './hooks/useTodos';

// Private (not exported)
// - TodoItem
// - TodoForm
// - todoService
```

### 5. Environment Configuration

```
src/
├── config/
│   ├── development.js
│   ├── production.js
│   ├── test.js
│   └── index.js
```

```javascript
// config/index.js
const env = process.env.NODE_ENV || 'development';

const configs = {
  development: require('./development'),
  production: require('./production'),
  test: require('./test')
};

export const config = configs[env];

// config/production.js
export default {
  apiUrl: process.env.REACT_APP_API_URL,
  enableAnalytics: true,
  logLevel: 'error'
};

// Usage
import { config } from '@/config';

fetch(config.apiUrl + '/users');
```

### 6. Separate Business Logic

```javascript
// Bad - logic in component
function UserProfile() {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    fetch('/api/user')
      .then(res => res.json())
      .then(data => setUser(data));
  }, []);
  
  return <div>{user?.name}</div>;
}

// Good - logic in hook
function useUser() {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    userService.getCurrent().then(setUser);
  }, []);
  
  return user;
}

function UserProfile() {
  const user = useUser();
  return <div>{user?.name}</div>;
}
```

### 7. Documentation

```javascript
/**
 * User profile component
 * 
 * Displays user information including name, email, and avatar.
 * Supports edit mode for updating user details.
 * 
 * @param {Object} props - Component props
 * @param {User} props.user - User object
 * @param {boolean} props.editable - Enable edit mode
 * @param {Function} props.onSave - Callback when user saves changes
 * 
 * @example
 * ```jsx
 * <UserProfile
 *   user={currentUser}
 *   editable={true}
 *   onSave={handleSave}
 * />
 * ```
 */
export function UserProfile({ user, editable, onSave }) {
  // Implementation
}
```

### 8. Type Safety

```typescript
// types/user.types.ts
export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user' | 'guest';
}

export interface UserFormData {
  name: string;
  email: string;
}

// components/UserProfile.tsx
import { User } from '@/types/user.types';

interface UserProfileProps {
  user: User;
  onEdit: (data: UserFormData) => void;
}

export function UserProfile({ user, onEdit }: UserProfileProps) {
  // Implementation
}
```
