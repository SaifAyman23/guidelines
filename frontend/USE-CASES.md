# React Frontend Use Cases

A comprehensive guide with practical instructions for common React development scenarios. Each use case provides step-by-step workflows, decision matrices, and best practices to help you build performant React applications.

## Table of Contents
- [Use Case 1: Starting a React Project](#use-case-1-starting-a-react-project)
- [Use Case 2: Building a New Feature](#use-case-2-building-a-new-feature)
- [Use Case 3: Managing Complex State](#use-case-3-managing-complex-state)
- [Use Case 4: Optimizing Performance](#use-case-4-optimizing-performance)
- [Use Case 5: Handling Forms and Validation](#use-case-5-handling-forms-and-validation)

---

## Use Case 1: Starting a React Project

### 🆚 Initial Setup: Vite vs Create React App

**Decision Matrix:**

| Feature | Vite | Create React App (CRA) |
|---------|------|------------------------|
| **Build Speed** | ⚡ Very Fast (esbuild) | 🐌 Slower (webpack) |
| **Dev Server** | ⚡ Instant HMR | 🐌 Slower HMR |
| **Bundle Size** | 📦 Smaller | 📦 Larger |
| **Configuration** | 🔧 Flexible | 🔒 Opinionated (needs eject) |
| **Modern Features** | ✅ Native ESM | ⚠️ Requires config |
| **Ecosystem** | 📈 Growing | 📊 Mature |
| **Recommendation** | ✅ **Recommended for new projects** | ⚠️ Legacy/existing projects |

### ⚡ Option 1: Vite (Recommended)

**Create Project:**

```bash
# Create new Vite project
npm create vite@latest my-app -- --template react

# Or with TypeScript
npm create vite@latest my-app -- --template react-ts

# Navigate to project
cd my-app

# Install dependencies
npm install
```

**Install Essential Dependencies:**

```bash
# Routing
npm install react-router-dom

# State Management (choose one based on needs)
npm install zustand  # Lightweight and simple
# OR
npm install @reduxjs/toolkit react-redux  # For complex state

# API Calls
npm install axios

# Form Handling
npm install react-hook-form

# Validation
npm install zod  # Works great with react-hook-form

# UI Components (optional, choose one)
npm install @mui/material @emotion/react @emotion/styled  # Material-UI
# OR
npm install @chakra-ui/react @emotion/react @emotion/styled framer-motion  # Chakra UI

# Utility
npm install clsx  # Conditional classNames
npm install date-fns  # Date manipulation

# Development dependencies
npm install -D @types/node  # Node types for TypeScript
```

**Start Development Server:**

```bash
npm run dev
```

### ⚛️ Option 2: Create React App

```bash
# Create new CRA project
npx create-react-app my-app

# Or with TypeScript
npx create-react-app my-app --template typescript

# Navigate and start
cd my-app
npm start
```

### 📁 Project Structure Setup

**Recommended Structure:**

```
my-app/
├── public/
│   └── favicon.ico
├── src/
│   ├── assets/
│   │   ├── images/
│   │   └── styles/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Button.test.tsx
│   │   │   │   └── Button.module.css
│   │   │   └── Input/
│   │   └── layout/
│   │       ├── Header/
│   │       ├── Footer/
│   │       └── Sidebar/
│   ├── features/
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── services/
│   │   │   └── types.ts
│   │   └── posts/
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   └── useLocalStorage.ts
│   ├── pages/
│   │   ├── Home/
│   │   ├── About/
│   │   └── NotFound/
│   ├── services/
│   │   ├── api.ts
│   │   └── auth.ts
│   ├── store/
│   │   ├── slices/
│   │   └── index.ts
│   ├── types/
│   │   └── index.ts
│   ├── utils/
│   │   ├── constants.ts
│   │   └── helpers.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── .env
├── .env.example
├── .gitignore
├── .eslintrc.cjs
├── .prettierrc
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

### 🔧 ESLint and Prettier Configuration

**Install ESLint and Prettier:**

```bash
npm install -D eslint prettier eslint-config-prettier eslint-plugin-prettier
npm install -D @typescript-eslint/eslint-plugin @typescript-eslint/parser
npm install -D eslint-plugin-react eslint-plugin-react-hooks
```

**Create `.eslintrc.cjs`:**

```javascript
module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:prettier/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['react', '@typescript-eslint', 'prettier'],
  rules: {
    'react/react-in-jsx-scope': 'off', // Not needed in React 17+
    'react/prop-types': 'off', // Using TypeScript
    '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
    'prettier/prettier': 'warn',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};
```

**Create `.prettierrc`:**

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "arrowParens": "avoid",
  "endOfLine": "lf"
}
```

**Add scripts to `package.json`:**

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .ts,.tsx",
    "lint:fix": "eslint . --ext .ts,.tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,css,md}\""
  }
}
```

### 🌍 Environment Variables Setup

**Create `.env` file:**

```bash
# .env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_NAME=My App
VITE_ENABLE_ANALYTICS=false
```

**Create `.env.example`:**

```bash
# .env.example
VITE_API_BASE_URL=
VITE_APP_NAME=
VITE_ENABLE_ANALYTICS=
```

**⚠️ Important:** In Vite, environment variables must be prefixed with `VITE_`

**Access in code:**

```typescript
// src/config.ts
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL,
  appName: import.meta.env.VITE_APP_NAME,
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
};
```

### 🚀 Initial App Setup

**Create basic routing (`src/App.tsx`):**

```typescript
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './pages/Home';
import About from './pages/About';
import NotFound from './pages/NotFound';
import Layout from './components/layout/Layout';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
```

**Create API service (`src/services/api.ts`):**

```typescript
import axios from 'axios';
import { config } from '../config';

const api = axios.create({
  baseURL: config.apiBaseUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### ✅ Setup Verification Checklist

- [ ] Project created with Vite or CRA
- [ ] Essential dependencies installed
- [ ] Project structure organized
- [ ] ESLint and Prettier configured
- [ ] Environment variables setup
- [ ] Basic routing configured
- [ ] API service created
- [ ] Git initialized and `.gitignore` configured
- [ ] Development server running successfully

---

## Use Case 2: Building a New Feature

### 🎯 Component Workflow

**Step-by-Step Process for Building a Blog Post Feature:**

### Step 1: Break Down UI into Components

**Component Hierarchy:**

```
BlogPostPage
├── Header
├── BlogPostList
│   └── BlogPostCard (repeated)
│       ├── PostImage
│       ├── PostTitle
│       ├── PostMeta
│       └── PostActions
└── Pagination
```

**💡 Tip:** Draw the UI on paper or use a tool like Excalidraw to identify component boundaries.

### Step 2: Props vs State Decisions

**Decision Matrix:**

| Use State When | Use Props When |
|----------------|----------------|
| Data changes over time | Data is passed from parent |
| User interactions modify it | Component displays but doesn't own data |
| Not passed from parent | Configuration or callbacks |
| Triggers re-renders | Read-only information |

**Example:**

```typescript
// BlogPostCard.tsx
interface BlogPostCardProps {
  // Props: Data from parent
  id: string;
  title: string;
  excerpt: string;
  author: string;
  publishedAt: string;
  imageUrl: string;
  onLike: (id: string) => void;  // Callback
}

function BlogPostCard({ 
  id, 
  title, 
  excerpt, 
  author, 
  publishedAt, 
  imageUrl, 
  onLike 
}: BlogPostCardProps) {
  // State: Component-owned data that changes
  const [isExpanded, setIsExpanded] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  
  return (
    <article className="blog-post-card">
      <img 
        src={imageUrl} 
        alt={title}
        onLoad={() => setImageLoaded(true)}
        className={imageLoaded ? 'loaded' : 'loading'}
      />
      <h2>{title}</h2>
      <p>{isExpanded ? excerpt : excerpt.slice(0, 100) + '...'}</p>
      <button onClick={() => setIsExpanded(!isExpanded)}>
        {isExpanded ? 'Read Less' : 'Read More'}
      </button>
      <button onClick={() => onLike(id)}>Like</button>
    </article>
  );
}
```

### Step 3: API Integration

**Create feature-specific API service:**

```typescript
// src/features/posts/services/postsApi.ts
import api from '@/services/api';
import { Post, CreatePostDto, UpdatePostDto } from '../types';

export const postsApi = {
  // Get all posts
  async getAllPosts(page = 1, limit = 10) {
    const response = await api.get<{ results: Post[]; count: number }>(
      `/posts/?page=${page}&limit=${limit}`
    );
    return response.data;
  },
  
  // Get single post
  async getPost(id: string) {
    const response = await api.get<Post>(`/posts/${id}/`);
    return response.data;
  },
  
  // Create post
  async createPost(data: CreatePostDto) {
    const response = await api.post<Post>('/posts/', data);
    return response.data;
  },
  
  // Update post
  async updatePost(id: string, data: UpdatePostDto) {
    const response = await api.patch<Post>(`/posts/${id}/`, data);
    return response.data;
  },
  
  // Delete post
  async deletePost(id: string) {
    await api.delete(`/posts/${id}/`);
  },
};
```

**Create custom hook for data fetching:**

```typescript
// src/features/posts/hooks/usePosts.ts
import { useState, useEffect } from 'react';
import { postsApi } from '../services/postsApi';
import { Post } from '../types';

export function usePosts(page = 1) {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  
  useEffect(() => {
    const fetchPosts = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await postsApi.getAllPosts(page);
        setPosts(data.results);
        setTotalCount(data.count);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch posts');
      } finally {
        setLoading(false);
      }
    };
    
    fetchPosts();
  }, [page]);
  
  return { posts, loading, error, totalCount };
}

// Usage in component
function BlogPostList() {
  const [page, setPage] = useState(1);
  const { posts, loading, error, totalCount } = usePosts(page);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      {posts.map(post => (
        <BlogPostCard key={post.id} {...post} />
      ))}
      <Pagination 
        currentPage={page} 
        total={totalCount}
        onPageChange={setPage}
      />
    </div>
  );
}
```

### Step 4: Error Boundary Implementation

**Create Error Boundary:**

```typescript
// src/components/common/ErrorBoundary/ErrorBoundary.tsx
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Log to error reporting service (e.g., Sentry)
  }
  
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}>
            Try again
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}

export default ErrorBoundary;
```

**Use Error Boundary:**

```typescript
// src/App.tsx
import ErrorBoundary from './components/common/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route 
            path="/posts" 
            element={
              <ErrorBoundary fallback={<div>Failed to load posts</div>}>
                <BlogPostList />
              </ErrorBoundary>
            } 
          />
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}
```

### 🏗️ Complete Feature Example

```typescript
// src/features/posts/types.ts
export interface Post {
  id: string;
  title: string;
  slug: string;
  content: string;
  excerpt: string;
  author: {
    id: string;
    name: string;
    email: string;
  };
  status: 'draft' | 'published';
  publishedAt: string;
  createdAt: string;
  updatedAt: string;
  imageUrl?: string;
}

export interface CreatePostDto {
  title: string;
  content: string;
  status?: 'draft' | 'published';
}

export interface UpdatePostDto extends Partial<CreatePostDto> {}

// src/features/posts/components/BlogPostCard.tsx
import React from 'react';
import { Post } from '../types';
import styles from './BlogPostCard.module.css';

interface BlogPostCardProps {
  post: Post;
  onLike?: (id: string) => void;
}

export function BlogPostCard({ post, onLike }: BlogPostCardProps) {
  return (
    <article className={styles.card}>
      {post.imageUrl && (
        <img src={post.imageUrl} alt={post.title} className={styles.image} />
      )}
      <div className={styles.content}>
        <h3 className={styles.title}>{post.title}</h3>
        <p className={styles.excerpt}>{post.excerpt}</p>
        <div className={styles.meta}>
          <span>By {post.author.name}</span>
          <span>{new Date(post.publishedAt).toLocaleDateString()}</span>
        </div>
        {onLike && (
          <button onClick={() => onLike(post.id)} className={styles.likeBtn}>
            ❤️ Like
          </button>
        )}
      </div>
    </article>
  );
}

// src/features/posts/pages/BlogPostsPage.tsx
import React, { useState } from 'react';
import { usePosts } from '../hooks/usePosts';
import { BlogPostCard } from '../components/BlogPostCard';
import { Pagination } from '@/components/common/Pagination';

export function BlogPostsPage() {
  const [page, setPage] = useState(1);
  const { posts, loading, error, totalCount } = usePosts(page);
  
  if (loading) {
    return <div className="loading">Loading posts...</div>;
  }
  
  if (error) {
    return <div className="error">Error: {error}</div>;
  }
  
  return (
    <div className="blog-posts-page">
      <h1>Blog Posts</h1>
      <div className="posts-grid">
        {posts.map(post => (
          <BlogPostCard key={post.id} post={post} />
        ))}
      </div>
      <Pagination
        currentPage={page}
        totalItems={totalCount}
        itemsPerPage={10}
        onPageChange={setPage}
      />
    </div>
  );
}
```

---

## Use Case 3: Managing Complex State

### 🌳 State Management Decision Matrix

```
Application State Complexity
│
├─ Simple (2-3 components share state)
│   └─ Use: useState + Props drilling
│       ├─ Pros: Simple, no dependencies
│       └─ Cons: Props drilling, component coupling
│
├─ Medium (4-8 components, 1-2 levels deep)
│   └─ Use: useContext + useReducer
│       ├─ Pros: Built-in, avoids props drilling
│       └─ Cons: Can cause unnecessary re-renders
│
├─ Medium-Complex (Component-local complex state)
│   └─ Use: useReducer
│       ├─ Pros: Predictable state updates
│       └─ Cons: More boilerplate
│
└─ Complex (Large app, many features)
    ├─ Option 1: Zustand (Recommended)
    │   ├─ Pros: Simple API, no boilerplate, great DevTools
    │   └─ Cons: Less mature than Redux
    │
    └─ Option 2: Redux Toolkit
        ├─ Pros: Mature, great DevTools, middleware ecosystem
        └─ Cons: More boilerplate, steeper learning curve
```

### 📊 useState (Simple State)

**When to Use:**
- Component-local state
- Simple data (boolean, string, number)
- State doesn't need to be shared

```typescript
function Counter() {
  const [count, setCount] = useState(0);
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <button onClick={() => setCount(prev => prev - 1)}>Decrement</button>
    </div>
  );
}

// Complex state object
function UserProfile() {
  const [user, setUser] = useState({
    name: '',
    email: '',
    bio: '',
  });
  
  const updateField = (field: string, value: string) => {
    setUser(prev => ({ ...prev, [field]: value }));
  };
  
  return (
    <form>
      <input 
        value={user.name}
        onChange={e => updateField('name', e.target.value)}
      />
      <input 
        value={user.email}
        onChange={e => updateField('email', e.target.value)}
      />
      <textarea 
        value={user.bio}
        onChange={e => updateField('bio', e.target.value)}
      />
    </form>
  );
}
```

### 🔄 useReducer (Complex Component State)

**When to Use:**
- Complex state logic
- Multiple sub-values
- Next state depends on previous
- State transitions need to be predictable

```typescript
// Types
type State = {
  posts: Post[];
  loading: boolean;
  error: string | null;
  filter: 'all' | 'published' | 'draft';
};

type Action =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: Post[] }
  | { type: 'FETCH_ERROR'; payload: string }
  | { type: 'SET_FILTER'; payload: 'all' | 'published' | 'draft' }
  | { type: 'ADD_POST'; payload: Post }
  | { type: 'DELETE_POST'; payload: string };

// Reducer
function postsReducer(state: State, action: Action): State {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, loading: true, error: null };
    
    case 'FETCH_SUCCESS':
      return { ...state, loading: false, posts: action.payload };
    
    case 'FETCH_ERROR':
      return { ...state, loading: false, error: action.payload };
    
    case 'SET_FILTER':
      return { ...state, filter: action.payload };
    
    case 'ADD_POST':
      return { ...state, posts: [...state.posts, action.payload] };
    
    case 'DELETE_POST':
      return {
        ...state,
        posts: state.posts.filter(post => post.id !== action.payload),
      };
    
    default:
      return state;
  }
}

// Component
function PostsManager() {
  const [state, dispatch] = useReducer(postsReducer, {
    posts: [],
    loading: false,
    error: null,
    filter: 'all',
  });
  
  useEffect(() => {
    const fetchPosts = async () => {
      dispatch({ type: 'FETCH_START' });
      try {
        const data = await postsApi.getAllPosts();
        dispatch({ type: 'FETCH_SUCCESS', payload: data.results });
      } catch (error) {
        dispatch({ type: 'FETCH_ERROR', payload: 'Failed to fetch posts' });
      }
    };
    
    fetchPosts();
  }, []);
  
  const filteredPosts = state.posts.filter(post => {
    if (state.filter === 'all') return true;
    return post.status === state.filter;
  });
  
  return (
    <div>
      <select 
        value={state.filter}
        onChange={e => dispatch({ 
          type: 'SET_FILTER', 
          payload: e.target.value as any 
        })}
      >
        <option value="all">All</option>
        <option value="published">Published</option>
        <option value="draft">Draft</option>
      </select>
      
      {state.loading && <div>Loading...</div>}
      {state.error && <div>Error: {state.error}</div>}
      
      {filteredPosts.map(post => (
        <div key={post.id}>
          <h3>{post.title}</h3>
          <button 
            onClick={() => dispatch({ type: 'DELETE_POST', payload: post.id })}
          >
            Delete
          </button>
        </div>
      ))}
    </div>
  );
}
```

### 🌐 Context API (Avoiding Props Drilling)

**When to Use:**
- Theme, language, authentication
- Data needed by many components
- Avoid props drilling

```typescript
// src/contexts/AuthContext.tsx
import { createContext, useContext, useState, ReactNode } from 'react';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  
  const login = async (email: string, password: string) => {
    // API call
    const response = await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    const data = await response.json();
    setUser(data.user);
    localStorage.setItem('token', data.token);
  };
  
  const logout = () => {
    setUser(null);
    localStorage.removeItem('token');
  };
  
  return (
    <AuthContext.Provider 
      value={{ 
        user, 
        login, 
        logout, 
        isAuthenticated: !!user 
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}

// Usage
function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/profile" element={<Profile />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

function Profile() {
  const { user, logout } = useAuth();
  
  return (
    <div>
      <h1>Welcome, {user?.name}</h1>
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### 🐻 Zustand (Recommended for Complex State)

**Installation:**

```bash
npm install zustand
```

**Create Store:**

```typescript
// src/store/postsStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { Post } from '@/types';
import { postsApi } from '@/services/postsApi';

interface PostsState {
  posts: Post[];
  loading: boolean;
  error: string | null;
  filter: 'all' | 'published' | 'draft';
  
  // Actions
  fetchPosts: () => Promise<void>;
  addPost: (post: Post) => void;
  deletePost: (id: string) => void;
  setFilter: (filter: 'all' | 'published' | 'draft') => void;
}

export const usePostsStore = create<PostsState>()(
  devtools(
    persist(
      (set, get) => ({
        posts: [],
        loading: false,
        error: null,
        filter: 'all',
        
        fetchPosts: async () => {
          set({ loading: true, error: null });
          try {
            const data = await postsApi.getAllPosts();
            set({ posts: data.results, loading: false });
          } catch (error) {
            set({ 
              error: error instanceof Error ? error.message : 'Failed to fetch',
              loading: false 
            });
          }
        },
        
        addPost: (post) => {
          set((state) => ({ posts: [...state.posts, post] }));
        },
        
        deletePost: (id) => {
          set((state) => ({
            posts: state.posts.filter((post) => post.id !== id),
          }));
        },
        
        setFilter: (filter) => {
          set({ filter });
        },
      }),
      { name: 'posts-storage' }
    )
  )
);

// Selectors for better performance
export const selectFilteredPosts = (state: PostsState) => {
  if (state.filter === 'all') return state.posts;
  return state.posts.filter(post => post.status === state.filter);
};
```

**Use in Components:**

```typescript
function PostsList() {
  const posts = usePostsStore(selectFilteredPosts);
  const { loading, error, fetchPosts, deletePost } = usePostsStore();
  
  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  
  return (
    <div>
      {posts.map(post => (
        <div key={post.id}>
          <h3>{post.title}</h3>
          <button onClick={() => deletePost(post.id)}>Delete</button>
        </div>
      ))}
    </div>
  );
}

function FilterButtons() {
  const { filter, setFilter } = usePostsStore();
  
  return (
    <div>
      <button onClick={() => setFilter('all')}>All</button>
      <button onClick={() => setFilter('published')}>Published</button>
      <button onClick={() => setFilter('draft')}>Draft</button>
    </div>
  );
}
```

### 🔴 Redux Toolkit (Enterprise Applications)

**Installation:**

```bash
npm install @reduxjs/toolkit react-redux
```

**Create Store:**

```typescript
// src/store/slices/postsSlice.ts
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { postsApi } from '@/services/postsApi';
import { Post } from '@/types';

interface PostsState {
  posts: Post[];
  loading: boolean;
  error: string | null;
}

export const fetchPosts = createAsyncThunk('posts/fetchPosts', async () => {
  const data = await postsApi.getAllPosts();
  return data.results;
});

const postsSlice = createSlice({
  name: 'posts',
  initialState: {
    posts: [],
    loading: false,
    error: null,
  } as PostsState,
  reducers: {
    addPost: (state, action: PayloadAction<Post>) => {
      state.posts.push(action.payload);
    },
    deletePost: (state, action: PayloadAction<string>) => {
      state.posts = state.posts.filter(post => post.id !== action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPosts.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPosts.fulfilled, (state, action) => {
        state.loading = false;
        state.posts = action.payload;
      })
      .addCase(fetchPosts.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch posts';
      });
  },
});

export const { addPost, deletePost } = postsSlice.actions;
export default postsSlice.reducer;

// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import postsReducer from './slices/postsSlice';

export const store = configureStore({
  reducer: {
    posts: postsReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// src/store/hooks.ts
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import type { RootState, AppDispatch } from './index';

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

**Use in App:**

```typescript
// src/main.tsx
import { Provider } from 'react-redux';
import { store } from './store';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <Provider store={store}>
    <App />
  </Provider>
);

// In components
function PostsList() {
  const dispatch = useAppDispatch();
  const { posts, loading, error } = useAppSelector(state => state.posts);
  
  useEffect(() => {
    dispatch(fetchPosts());
  }, [dispatch]);
  
  return (
    <div>
      {posts.map(post => (
        <div key={post.id}>
          <h3>{post.title}</h3>
          <button onClick={() => dispatch(deletePost(post.id))}>
            Delete
          </button>
        </div>
      ))}
    </div>
  );
}
```

---

## Use Case 4: Optimizing Performance

### 🔍 Profiling with React DevTools

**Installation:**

1. Install React DevTools browser extension
2. Open DevTools → Profiler tab

**How to Profile:**

```typescript
// 1. Click Record
// 2. Interact with your app
// 3. Click Stop
// 4. Analyze the flame graph
```

**What to look for:**
- 🔴 Long render times (yellow/red bars)
- 🔄 Unnecessary re-renders
- 📊 Component render frequency

### 🎯 Identifying Unnecessary Re-renders

**Common causes:**

1. **Inline function definitions**
2. **Inline object/array creation**
3. **Missing dependency arrays**
4. **Parent component re-renders**

**Detection tool:**

```typescript
// Custom hook to track re-renders
function useRenderCount(componentName: string) {
  const renderCount = useRef(0);
  
  useEffect(() => {
    renderCount.current += 1;
    console.log(`${componentName} rendered ${renderCount.current} times`);
  });
}

// Usage
function MyComponent() {
  useRenderCount('MyComponent');
  // ... component logic
}
```

### ⚛️ Using React.memo

**When to Use:**
- Component renders often with same props
- Component is expensive to render
- Parent re-renders frequently

```typescript
// Without memo - re-renders every time parent re-renders
function ExpensiveComponent({ data }: { data: string }) {
  console.log('Rendering ExpensiveComponent');
  // Expensive computation
  return <div>{data}</div>;
}

// With memo - only re-renders when props change
const ExpensiveComponent = React.memo(({ data }: { data: string }) => {
  console.log('Rendering ExpensiveComponent');
  return <div>{data}</div>;
});

// Custom comparison function
const ExpensiveComponent = React.memo(
  ({ user }: { user: User }) => {
    return <div>{user.name}</div>;
  },
  (prevProps, nextProps) => {
    // Return true if props are equal (skip render)
    return prevProps.user.id === nextProps.user.id;
  }
);
```

### 🔄 useCallback and useMemo

**useCallback - Memoize Functions:**

```typescript
function ParentComponent() {
  const [count, setCount] = useState(0);
  const [items, setItems] = useState<string[]>([]);
  
  // ❌ BAD: Function recreated on every render
  const handleClick = () => {
    console.log('Clicked');
  };
  
  // ✅ GOOD: Function memoized
  const handleClick = useCallback(() => {
    console.log('Clicked');
  }, []); // Only recreated if dependencies change
  
  // With dependencies
  const handleAddItem = useCallback((item: string) => {
    setItems(prev => [...prev, item]);
  }, []); // setItems is stable, no dependencies needed
  
  return (
    <>
      <button onClick={() => setCount(count + 1)}>Count: {count}</button>
      <ChildComponent onClick={handleClick} />
    </>
  );
}

const ChildComponent = React.memo(({ onClick }: { onClick: () => void }) => {
  console.log('Child rendered');
  return <button onClick={onClick}>Click me</button>;
});
```

**useMemo - Memoize Values:**

```typescript
function SearchableList({ items, query }: { items: Item[]; query: string }) {
  // ❌ BAD: Filtered on every render
  const filteredItems = items.filter(item => 
    item.name.toLowerCase().includes(query.toLowerCase())
  );
  
  // ✅ GOOD: Only recalculate when items or query changes
  const filteredItems = useMemo(
    () => items.filter(item => 
      item.name.toLowerCase().includes(query.toLowerCase())
    ),
    [items, query]
  );
  
  return (
    <ul>
      {filteredItems.map(item => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  );
}

// Expensive calculation
function DataProcessor({ data }: { data: number[] }) {
  const processedData = useMemo(() => {
    console.log('Processing data...');
    return data
      .map(n => n * 2)
      .filter(n => n > 10)
      .reduce((a, b) => a + b, 0);
  }, [data]);
  
  return <div>Result: {processedData}</div>;
}
```

**⚠️ When NOT to use useMemo/useCallback:**
- Simple calculations (overhead > benefit)
- Props that change frequently
- Premature optimization

### 📦 Code Splitting and Lazy Loading

**Route-based Code Splitting:**

```typescript
import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Lazy load components
const Home = lazy(() => import('./pages/Home'));
const About = lazy(() => import('./pages/About'));
const Dashboard = lazy(() => import('./pages/Dashboard'));

function App() {
  return (
    <Router>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </Suspense>
    </Router>
  );
}
```

**Component-based Code Splitting:**

```typescript
import { lazy, Suspense } from 'react';

const HeavyChart = lazy(() => import('./components/HeavyChart'));

function Dashboard() {
  const [showChart, setShowChart] = useState(false);
  
  return (
    <div>
      <button onClick={() => setShowChart(true)}>Show Chart</button>
      
      {showChart && (
        <Suspense fallback={<div>Loading chart...</div>}>
          <HeavyChart />
        </Suspense>
      )}
    </div>
  );
}
```

**Named Exports:**

```typescript
// If component is not default export
const MyComponent = lazy(() => 
  import('./components').then(module => ({ 
    default: module.MyComponent 
  }))
);
```

### 📊 Bundle Size Optimization

**Analyze Bundle:**

```bash
# Vite
npm run build
npx vite-bundle-visualizer

# Or use rollup-plugin-visualizer
npm install -D rollup-plugin-visualizer
```

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
});
```

**Optimization Techniques:**

1. **Tree Shaking - Import only what you need:**

```typescript
// ❌ BAD: Imports entire library
import _ from 'lodash';
const result = _.debounce(fn, 300);

// ✅ GOOD: Import only needed function
import debounce from 'lodash/debounce';
const result = debounce(fn, 300);

// ✅ BETTER: Use smaller alternatives
import { debounce } from 'es-toolkit';
```

2. **Use Production Builds:**

```bash
# Always use production build for deployment
npm run build
```

3. **Remove Unused Dependencies:**

```bash
# Analyze dependencies
npx depcheck

# Remove unused packages
npm uninstall package-name
```

4. **Dynamic Imports:**

```typescript
// Load library only when needed
async function handleExport() {
  const { saveAs } = await import('file-saver');
  saveAs(blob, 'export.csv');
}
```

### 🚀 Performance Checklist

- [ ] Use React DevTools Profiler to identify bottlenecks
- [ ] Wrap expensive components with `React.memo`
- [ ] Use `useCallback` for functions passed to memoized child components
- [ ] Use `useMemo` for expensive calculations
- [ ] Implement code splitting for routes
- [ ] Lazy load heavy components
- [ ] Optimize images (WebP, lazy loading)
- [ ] Use production build
- [ ] Analyze and optimize bundle size
- [ ] Virtualize long lists (react-window)
- [ ] Debounce/throttle frequent events

---

## Use Case 5: Handling Forms and Validation

### 🎛️ Controlled vs Uncontrolled Components

**Controlled Components (Recommended):**

```typescript
function ControlledForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log({ email, password });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}  // React controls the value
        onChange={e => setEmail(e.target.value)}
      />
      <input
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
      />
      <button type="submit">Submit</button>
    </form>
  );
}
```

**Uncontrolled Components:**

```typescript
function UncontrolledForm() {
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log({
      email: emailRef.current?.value,
      password: passwordRef.current?.value,
    });
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input type="email" ref={emailRef} defaultValue="" />
      <input type="password" ref={passwordRef} defaultValue="" />
      <button type="submit">Submit</button>
    </form>
  );
}
```

**When to Use:**
- ✅ **Controlled:** Default choice, validation, dynamic inputs
- ⚠️ **Uncontrolled:** File inputs, integrating with non-React code

### 📚 Form Libraries Comparison

| Feature | React Hook Form | Formik |
|---------|----------------|--------|
| **Performance** | ⚡ Excellent (uncontrolled) | 🐌 Good (controlled) |
| **Bundle Size** | 📦 9.4kb | 📦 15.5kb |
| **Re-renders** | ✅ Minimal | ⚠️ More frequent |
| **TypeScript** | ✅ Excellent | ✅ Good |
| **Validation** | ✅ Built-in + External | ✅ Built-in + Yup |
| **Learning Curve** | 📈 Gentle | 📈 Moderate |
| **Recommendation** | ✅ **Recommended** | ⚠️ Good alternative |

### 🎣 React Hook Form (Recommended)

**Installation:**

```bash
npm install react-hook-form zod @hookform/resolvers
```

**Basic Form:**

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';

// Define schema
const schema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  confirmPassword: z.string(),
}).refine(data => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type FormData = z.infer<typeof schema>;

function RegistrationForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });
  
  const onSubmit = async (data: FormData) => {
    try {
      await api.post('/register', data);
      console.log('Success!');
    } catch (error) {
      console.error('Error:', error);
    }
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <input
          type="email"
          {...register('email')}
          placeholder="Email"
        />
        {errors.email && <span>{errors.email.message}</span>}
      </div>
      
      <div>
        <input
          type="password"
          {...register('password')}
          placeholder="Password"
        />
        {errors.password && <span>{errors.password.message}</span>}
      </div>
      
      <div>
        <input
          type="password"
          {...register('confirmPassword')}
          placeholder="Confirm Password"
        />
        {errors.confirmPassword && <span>{errors.confirmPassword.message}</span>}
      </div>
      
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Submitting...' : 'Submit'}
      </button>
    </form>
  );
}
```

### ✅ Client-side Validation Patterns

**Field-level Validation:**

```typescript
const schema = z.object({
  username: z
    .string()
    .min(3, 'Minimum 3 characters')
    .max(20, 'Maximum 20 characters')
    .regex(/^[a-zA-Z0-9_]+$/, 'Only letters, numbers, and underscores'),
  
  age: z
    .number()
    .min(18, 'Must be 18 or older')
    .max(120, 'Invalid age'),
  
  website: z
    .string()
    .url('Invalid URL')
    .optional()
    .or(z.literal('')),
});
```

**Custom Validation:**

```typescript
const schema = z.object({
  email: z.string().email(),
  username: z.string().refine(
    async (username) => {
      const response = await api.get(`/check-username/${username}`);
      return response.data.available;
    },
    { message: 'Username already taken' }
  ),
});
```

### 🔗 Server-side Validation Integration

```typescript
function RegistrationForm() {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });
  
  const onSubmit = async (data: FormData) => {
    try {
      await api.post('/register', data);
    } catch (error: any) {
      // Handle server validation errors
      if (error.response?.data?.errors) {
        Object.entries(error.response.data.errors).forEach(([field, message]) => {
          setError(field as keyof FormData, {
            type: 'server',
            message: message as string,
          });
        });
      }
    }
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Form fields */}
    </form>
  );
}
```

### 📁 File Upload Handling

```typescript
interface FileUploadFormData {
  file: FileList;
  description: string;
}

function FileUploadForm() {
  const { register, handleSubmit, watch } = useForm<FileUploadFormData>();
  const file = watch('file');
  
  const onSubmit = async (data: FileUploadFormData) => {
    const formData = new FormData();
    formData.append('file', data.file[0]);
    formData.append('description', data.description);
    
    try {
      await api.post('/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input
        type="file"
        {...register('file', {
          required: 'File is required',
          validate: {
            fileSize: (files) => 
              files[0]?.size < 5000000 || 'Max file size is 5MB',
            fileType: (files) => 
              ['image/jpeg', 'image/png'].includes(files[0]?.type) ||
              'Only JPEG and PNG files are allowed',
          },
        })}
      />
      
      {file?.[0] && (
        <div>
          <p>Selected: {file[0].name}</p>
          <p>Size: {(file[0].size / 1024).toFixed(2)} KB</p>
        </div>
      )}
      
      <textarea {...register('description')} />
      
      <button type="submit">Upload</button>
    </form>
  );
}
```

### 🎯 Multi-step Forms

```typescript
import { useState } from 'react';
import { useForm, FormProvider, useFormContext } from 'react-hook-form';

// Step 1
function PersonalInfo() {
  const { register, formState: { errors } } = useFormContext();
  
  return (
    <div>
      <input {...register('firstName', { required: 'Required' })} />
      {errors.firstName && <span>{errors.firstName.message}</span>}
      
      <input {...register('lastName', { required: 'Required' })} />
      {errors.lastName && <span>{errors.lastName.message}</span>}
    </div>
  );
}

// Step 2
function ContactInfo() {
  const { register, formState: { errors } } = useFormContext();
  
  return (
    <div>
      <input {...register('email', { required: 'Required' })} />
      {errors.email && <span>{errors.email.message}</span>}
      
      <input {...register('phone', { required: 'Required' })} />
      {errors.phone && <span>{errors.phone.message}</span>}
    </div>
  );
}

// Step 3
function Review() {
  const { watch } = useFormContext();
  const formData = watch();
  
  return (
    <div>
      <h3>Review Your Information</h3>
      <p>Name: {formData.firstName} {formData.lastName}</p>
      <p>Email: {formData.email}</p>
      <p>Phone: {formData.phone}</p>
    </div>
  );
}

// Main Form
function MultiStepForm() {
  const [step, setStep] = useState(1);
  const methods = useForm();
  
  const onSubmit = async (data: any) => {
    console.log('Final data:', data);
    await api.post('/submit', data);
  };
  
  const nextStep = async () => {
    const isValid = await methods.trigger(); // Validate current step
    if (isValid) setStep(step + 1);
  };
  
  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        <div className="progress">
          Step {step} of 3
        </div>
        
        {step === 1 && <PersonalInfo />}
        {step === 2 && <ContactInfo />}
        {step === 3 && <Review />}
        
        <div className="buttons">
          {step > 1 && (
            <button type="button" onClick={() => setStep(step - 1)}>
              Previous
            </button>
          )}
          
          {step < 3 ? (
            <button type="button" onClick={nextStep}>
              Next
            </button>
          ) : (
            <button type="submit">Submit</button>
          )}
        </div>
      </form>
    </FormProvider>
  );
}
```

### 🎨 Complete Form Example

```typescript
// src/components/CreatePostForm.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { postsApi } from '@/services/postsApi';
import styles from './CreatePostForm.module.css';

const schema = z.object({
  title: z.string().min(5, 'Title must be at least 5 characters'),
  content: z.string().min(50, 'Content must be at least 50 characters'),
  excerpt: z.string().max(200, 'Excerpt must be at most 200 characters'),
  status: z.enum(['draft', 'published']),
  image: z.any().optional(),
});

type FormData = z.infer<typeof schema>;

export function CreatePostForm({ onSuccess }: { onSuccess?: () => void }) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      status: 'draft',
    },
  });
  
  const onSubmit = async (data: FormData) => {
    try {
      await postsApi.createPost(data);
      reset();
      onSuccess?.();
    } catch (error) {
      console.error('Failed to create post:', error);
    }
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)} className={styles.form}>
      <div className={styles.field}>
        <label htmlFor="title">Title</label>
        <input
          id="title"
          type="text"
          {...register('title')}
          className={errors.title ? styles.error : ''}
        />
        {errors.title && (
          <span className={styles.errorMessage}>{errors.title.message}</span>
        )}
      </div>
      
      <div className={styles.field}>
        <label htmlFor="excerpt">Excerpt</label>
        <textarea
          id="excerpt"
          {...register('excerpt')}
          rows={3}
          className={errors.excerpt ? styles.error : ''}
        />
        {errors.excerpt && (
          <span className={styles.errorMessage}>{errors.excerpt.message}</span>
        )}
      </div>
      
      <div className={styles.field}>
        <label htmlFor="content">Content</label>
        <textarea
          id="content"
          {...register('content')}
          rows={10}
          className={errors.content ? styles.error : ''}
        />
        {errors.content && (
          <span className={styles.errorMessage}>{errors.content.message}</span>
        )}
      </div>
      
      <div className={styles.field}>
        <label htmlFor="status">Status</label>
        <select id="status" {...register('status')}>
          <option value="draft">Draft</option>
          <option value="published">Published</option>
        </select>
      </div>
      
      <div className={styles.actions}>
        <button type="button" onClick={() => reset()}>
          Reset
        </button>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating...' : 'Create Post'}
        </button>
      </div>
    </form>
  );
}
```

---

## Use Case 6: Production Deployment with Docker and Nginx

### 🐳 Containerizing React Application

**Why Use Docker for React?**
- ✅ Consistent environment across development and production
- ✅ Easy scaling and deployment
- ✅ Simplified dependency management
- ✅ Better integration with CI/CD pipelines

### 📦 Production Build Configuration

**Optimize Vite for Production:**

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { compression } from 'vite-plugin-compression2';

export default defineConfig({
  plugins: [
    react(),
    compression({ algorithm: 'gzip' }),
    compression({ algorithm: 'brotliCompress', exclude: [/\.(br)$/, /\.(gz)$/] }),
  ],
  build: {
    outDir: 'dist',
    sourcemap: false, // Disable for production
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.logs
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['@mui/material', '@emotion/react', '@emotion/styled'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  server: {
    port: 3000,
    host: true, // Listen on all addresses
  },
  preview: {
    port: 3000,
  },
});
```

### 🐋 Docker Setup

**Multi-stage Dockerfile (Recommended):**

```dockerfile
# Stage 1: Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Stage 2: Production stage with Nginx
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

**Development Dockerfile:**

```dockerfile
# Dockerfile.dev
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev)
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### 🌐 Nginx Configuration

**Basic Nginx Config (`nginx.conf`):**

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/javascript application/json
               image/svg+xml;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # API proxy (for backend)
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # React Router support - all routes go to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

**Advanced Nginx Config with SSL (Let's Encrypt):**

```nginx
# HTTP - redirect to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    root /usr/share/nginx/html;
    index index.html;
    
    # Gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/javascript application/json image/svg+xml;
    
    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # React Router
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### 🐙 Docker Compose

**Complete Docker Compose Setup:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: react-app
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - certbot-etc:/etc/letsencrypt
      - certbot-var:/var/lib/letsencrypt
    depends_on:
      - backend
    networks:
      - app-network

  # Backend (Django)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: django-api
    restart: unless-stopped
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - ./backend:/app
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    expose:
      - "8000"
    env_file:
      - ./backend/.env.production
    depends_on:
      - db
      - redis
    networks:
      - app-network

  # Database
  db:
    image: postgres:14-alpine
    container_name: postgres-db
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    networks:
      - app-network

  # Redis
  redis:
    image: redis:7-alpine
    container_name: redis-cache
    restart: unless-stopped
    networks:
      - app-network

  # Certbot for SSL
  certbot:
    image: certbot/certbot
    container_name: certbot
    volumes:
      - certbot-etc:/etc/letsencrypt
      - certbot-var:/var/lib/letsencrypt
      - ./frontend/dist:/var/www/html
    depends_on:
      - frontend
    command: certonly --webroot --webroot-path=/var/www/html --email your@email.com --agree-tos --no-eff-email --force-renewal -d yourdomain.com -d www.yourdomain.com

volumes:
  postgres_data:
  static_volume:
  media_volume:
  certbot-etc:
  certbot-var:

networks:
  app-network:
    driver: bridge
```

**Development Docker Compose:**

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: react-app-dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000/api/v1
    networks:
      - app-network

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    env_file:
      - ./backend/.env.development
    depends_on:
      - db
      - redis
    networks:
      - app-network

  db:
    image: postgres:14-alpine
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: myproject_dev
      POSTGRES_USER: dev_user
      POSTGRES_PASSWORD: dev_password
    ports:
      - "5432:5432"
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-network

volumes:
  postgres_data_dev:

networks:
  app-network:
    driver: bridge
```

### 📝 Environment Configuration

**Frontend `.env.production`:**

```bash
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
VITE_APP_NAME=My Production App
VITE_ENABLE_ANALYTICS=true
VITE_SENTRY_DSN=your-sentry-dsn
```

**Backend `.env.production`:**

```bash
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com
DATABASE_URL=postgresql://user:password@db:5432/dbname
REDIS_URL=redis://redis:6379/0
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### 🚀 Deployment Commands

**Build and Deploy:**

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f frontend

# Run database migrations
docker-compose exec backend python manage.py migrate

# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Restart specific service
docker-compose restart frontend

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Scale frontend
docker-compose up -d --scale frontend=3
```

**Development Commands:**

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up

# Install new npm package
docker-compose -f docker-compose.dev.yml exec frontend npm install package-name

# Run tests
docker-compose -f docker-compose.dev.yml exec frontend npm test
docker-compose -f docker-compose.dev.yml exec backend python manage.py test
```

### 📊 Monitoring and Logging

**Add Logging to Nginx:**

```nginx
# In nginx.conf
access_log /var/log/nginx/access.log combined;
error_log /var/log/nginx/error.log warn;

# Custom log format
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_referer" '
                '"$http_user_agent" "$http_x_forwarded_for"';
```

**View Logs:**

```bash
# Nginx access logs
docker-compose exec frontend tail -f /var/log/nginx/access.log

# Nginx error logs
docker-compose exec frontend tail -f /var/log/nginx/error.log

# Application logs
docker-compose logs -f --tail=100 frontend
docker-compose logs -f --tail=100 backend
```

### 🔒 Security Best Practices

**1. Use Non-Root User in Dockerfile:**

```dockerfile
# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Switch to non-root user
USER nodejs
```

**2. Scan for Vulnerabilities:**

```bash
# Scan Docker image
docker scan react-app:latest

# Scan npm dependencies
npm audit

# Fix vulnerabilities
npm audit fix
```

**3. Use Docker Secrets:**

```yaml
# docker-compose.yml
services:
  backend:
    secrets:
      - db_password
      - secret_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

### ✅ Deployment Checklist

- [ ] Environment variables configured
- [ ] Docker images built and tested
- [ ] Nginx configuration validated
- [ ] SSL certificates obtained (Let's Encrypt)
- [ ] Database migrations run
- [ ] Static files collected
- [ ] Health checks working
- [ ] Logs configured and accessible
- [ ] Security headers configured
- [ ] CORS configured correctly
- [ ] Monitoring and error tracking setup (Sentry)
- [ ] Backup strategy in place
- [ ] CI/CD pipeline configured

### 🎯 Production Optimization Tips

1. **Enable Brotli Compression** - Better than gzip
2. **Use CDN** - CloudFlare, AWS CloudFront for static assets
3. **Implement Rate Limiting** - Protect against DDoS
4. **Use HTTP/2** - Faster loading
5. **Lazy Load Images** - Reduce initial bundle size
6. **Service Worker** - Offline support and caching
7. **Preload Critical Resources** - Faster initial render

---

## 📚 Additional Resources

- [React Official Documentation](https://react.dev/)
- [Vite Guide](https://vitejs.dev/guide/)
- [React Hook Form](https://react-hook-form.com/)
- [Zustand Documentation](https://docs.pmnd.rs/zustand/)
- [Redux Toolkit](https://redux-toolkit.js.org/)
- [React Performance Optimization](https://react.dev/learn/render-and-commit)

---

## 🎯 Quick Reference

| Task | Tool/Pattern |
|------|-------------|
| Project Setup | Vite (recommended) or CRA |
| Routing | React Router |
| State (Simple) | useState + props |
| State (Medium) | useContext + useReducer |
| State (Complex) | Zustand or Redux Toolkit |
| Forms | React Hook Form + Zod |
| API Calls | Axios + custom hooks |
| Performance | React.memo, useCallback, useMemo |
| Code Splitting | React.lazy + Suspense |

---

**Remember:** These use cases are guidelines. Always consider your specific project requirements and team expertise when choosing tools and patterns.
