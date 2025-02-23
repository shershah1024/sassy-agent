# Google Slides Integration Guide

This guide explains how to use the Google Slides integration in your application, including authentication, token management, and creating/modifying presentations.

## Table of Contents
- [Authentication Setup](#authentication-setup)
- [Required Scopes](#required-scopes)
- [Token Management](#token-management)
- [Creating Presentations](#creating-presentations)
- [API Reference](#api-reference)
- [Error Handling](#error-handling)

## Authentication Setup

### 1. Environment Variables
```env
GOOGLE_ID=your_google_client_id
GOOGLE_SECRET=your_google_client_secret
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_nextauth_secret
```

### 2. Required Database Schema (Supabase)
```sql
CREATE TABLE user_auth (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at BIGINT NOT NULL,
    provider TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);
```

## Required Scopes

```typescript
const PRESENTATION_SCOPES = [
  'https://www.googleapis.com/auth/presentations',
  'https://www.googleapis.com/auth/presentations.readonly',
  'https://www.googleapis.com/auth/drive.file'
];
```

## Token Management

### 1. Getting a Valid Token
```typescript
async function getValidAccessToken(userId: string): Promise<string | null> {
  const { data: auth } = await supabase
    .from('user_auth')
    .select('*')
    .eq('user_id', userId)
    .single();

  if (!auth) return null;

  // Check if token is expired or will expire soon (within 5 minutes)
  const isExpiringSoon = auth.expires_at - 300 < Math.floor(Date.now() / 1000);
  
  if (isExpiringSoon) {
    // Token needs refresh
    const newTokens = await refreshGoogleToken(auth.refresh_token);
    if (!newTokens) return null;
    return newTokens.access_token;
  }

  return auth.access_token;
}
```

## Creating Presentations

### 1. Basic Presentation Creation
```typescript
async function createPresentation(title: string, accessToken: string) {
  const response = await fetch('https://slides.googleapis.com/v1/presentations', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: title
    })
  });

  return response.json();
}
```

### 2. Adding Slides with Content
```typescript
interface SlideContent {
  layout: string;
  title?: string;
  subtitle?: string;
  content?: string[];
  images?: string[];
}

async function addSlidesToPresentation(
  presentationId: string, 
  slides: SlideContent[], 
  accessToken: string
) {
  const requests = slides.map(slide => ({
    createSlide: {
      objectId: generateUniqueId(),
      slideLayoutReference: {
        predefinedLayout: slide.layout
      },
      placeholderIdMappings: [
        {
          layoutPlaceholder: { type: 'TITLE' },
          objectId: generateUniqueId()
        },
        {
          layoutPlaceholder: { type: 'BODY' },
          objectId: generateUniqueId()
        }
      ]
    }
  }));

  const response = await fetch(
    `https://slides.googleapis.com/v1/presentations/${presentationId}:batchUpdate`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ requests })
    }
  );

  return response.json();
}
```

### 3. Example Usage
```typescript
async function createFullPresentation(userId: string, title: string, content: SlideContent[]) {
  // 1. Get valid token
  const accessToken = await getValidAccessToken(userId);
  if (!accessToken) throw new Error('No valid access token');

  // 2. Create presentation
  const presentation = await createPresentation(title, accessToken);
  
  // 3. Add slides
  await addSlidesToPresentation(presentation.presentationId, content, accessToken);

  return presentation.presentationId;
}
```

## API Reference

### 1. Create Presentation Endpoint
```typescript
// app/api/presentations/route.ts
import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { title, slides } = await req.json();
    const { userId } = auth(); // Get authenticated user

    const presentationId = await createFullPresentation(userId, title, slides);

    return NextResponse.json({ presentationId });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to create presentation' },
      { status: 500 }
    );
  }
}
```

### 2. Client-Side Component
```typescript
'use client';

import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';

export function PresentationCreator() {
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const { session } = useAuth();

  const handleCreate = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/presentations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          slides: [
            {
              layout: 'TITLE',
              title: title,
              subtitle: 'Created with our application'
            }
          ]
        })
      });

      const data = await response.json();
      // Handle success
    } catch (error) {
      // Handle error
    } finally {
      setLoading(false);
    }
  };

  return (
    // Your presentation creation UI
  );
}
```

## Error Handling

### Common Errors and Solutions

1. Token Expired
```typescript
if (error.status === 401) {
  // Token expired - trigger refresh
  await refreshToken(userId);
  // Retry the operation
}
```

2. Permission Issues
```typescript
if (error.status === 403) {
  // Check if user has granted necessary scopes
  // Redirect to consent screen if needed
  signIn('google', { 
    callbackUrl: '/',
    prompt: 'consent'
  });
}
```

3. Rate Limiting
```typescript
if (error.status === 429) {
  // Implement exponential backoff
  await new Promise(resolve => setTimeout(resolve, 1000 * Math.random()));
  // Retry the operation
}
```

### Best Practices

1. Always verify token validity before making API calls
2. Implement proper error handling and retries
3. Use type-safe interfaces for all API calls
4. Maintain proper scopes and permissions
5. Implement rate limiting and quotas
6. Keep tokens secure and refresh them properly
7. Log errors and operations for debugging

## Additional Resources

- [Google Slides API Documentation](https://developers.google.com/slides/api/reference/rest)
- [NextAuth.js Documentation](https://next-auth.js.org/)
- [Supabase Documentation](https://supabase.io/docs) 