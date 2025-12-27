# STEP 7: FRONTEND INTEGRATION
**Report Date**: 14/12/2024  
**System Component**: React/Next.js Frontend  
**Development Phase**: Full-Stack Integration  

---

## EXECUTIVE SUMMARY

This report documents the implementation of the frontend chat interface for the Multi-Index RAG system. The frontend is built with Next.js 15 and provides a modern, responsive chat UI that integrates with the FastAPI backend.

**Key Achievements**:
- Next.js 15 with React 19 and Turbopack
- Modern chat interface with markdown support
- Real-time loading states and error handling
- Async backend refactoring for better performance

---

## 1. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15)                     │
│                                                              │
│   ChatPage → ChatMessages → MessageBubble                   │
│       │                          ↓                          │
│       └── API Client ────→ FastAPI Backend                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. TECHNOLOGY STACK

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | Next.js | 15.x |
| **React** | React | 19 |
| **Styling** | Vanilla CSS | - |
| **Markdown** | react-markdown | Latest |
| **Build** | Turbopack | Native |

---

## 3. KEY COMPONENTS

### 3.1. Chat Page

```typescript
// src/app/chat/page.tsx
export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(false);
    
    const handleSubmit = async (query: string) => {
        setLoading(true);
        const response = await queryAPI(query);
        setMessages([...messages, response]);
        setLoading(false);
    };
}
```

### 3.2. Message Bubble

- User messages (right-aligned, blue)
- Bot messages (left-aligned, gray)
- Markdown rendering for formatted answers
- Citation links

### 3.3. Input Form

```typescript
<form onSubmit={handleSubmit}>
    <input 
        type="text" 
        placeholder="Nhập câu hỏi..."
        disabled={loading}
    />
    <button type="submit" disabled={loading}>
        {loading ? "Đang xử lý..." : "Gửi"}
    </button>
</form>
```

---

## 4. CSS STYLING

### 4.1. Design System

```css
:root {
    --primary-color: #2563eb;
    --background: #f8fafc;
    --text-primary: #1e293b;
    --border-radius: 12px;
}
```

### 4.2. Responsive Design

- Mobile-first approach
- Breakpoints: 768px, 1024px
- Flexible chat container

---

## 5. FILES CREATED

```
frontend/
├── src/
│   ├── app/
│   │   ├── page.tsx         # Landing page
│   │   ├── chat/
│   │   │   └── page.tsx     # Chat interface
│   │   └── layout.tsx       # Root layout
│   ├── components/
│   │   ├── ChatMessages.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── InputForm.tsx
│   │   └── Navigation.tsx
│   ├── services/
│   │   └── api.ts           # API client
│   └── styles/
│       └── globals.css      # Global styles
├── package.json
└── next.config.js
```

---

## 6. BACKEND ASYNC REFACTORING

### 6.1. Changes Made

- Converted `run_rag_pipeline` to async
- Added `asyncio.gather` for parallel operations
- Improved timeout handling

### 6.2. Performance Impact

| Operation | Before | After |
|-----------|--------|-------|
| Pipeline execution | sync | async |
| Parallel retrieval | limited | full async |
| Frontend responsiveness | blocking | non-blocking |

---

## 7. COMMANDS

```bash
# Install dependencies
cd frontend
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

---

## 8. TEST RESULTS

| Feature | Status |
|---------|--------|
| Chat interface | ✅ Working |
| API integration | ✅ Working |
| Markdown rendering | ✅ Working |
| Loading states | ✅ Working |
| Error handling | ✅ Working |

---

## 9. NEXT STEPS

→ Step 8: Canonical Answer Framework (CAF)
→ Step 9: External Search Fallback
