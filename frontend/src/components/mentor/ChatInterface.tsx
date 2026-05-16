'use client';

import React, { useState, useEffect, useRef } from 'react';
import { chatApi } from '@/lib/api';
import type { ChatMessage } from '@/lib/types';

interface Props {
  submissionId: string;
}

const STARTER_QUESTIONS = [
  'How can I improve my code structure?',
  'What does my evaluation score mean?',
  'What are the biggest weaknesses in my project?',
  'How does my project compare to best practices?',
];

function renderContent(text: string): JSX.Element {
  const parts = text.split(/(```[\s\S]*?```|`[^`]+`|\*\*[^*]+\*\*)/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          const code = part.slice(3, -3).replace(/^[^\n]*\n/, '');
          return (
            <pre
              key={i}
              className="mt-2 mb-2 p-3 bg-[#13141a] border border-[#3a3b48] rounded-md text-xs font-mono text-brand-300 overflow-x-auto whitespace-pre-wrap"
            >
              {code}
            </pre>
          );
        }
        if (part.startsWith('`') && part.endsWith('`')) {
          return (
            <code key={i} className="px-1 py-0.5 bg-[#252630] rounded text-xs font-mono text-brand-300">
              {part.slice(1, -1)}
            </code>
          );
        }
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={i} className="font-semibold text-white">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

export function ChatInterface({ submissionId }: Props) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    chatApi
      .createOrGetSession(submissionId)
      .then((session) => {
        setSessionId(session.id);
        setMessages(session.messages ?? []);
      })
      .catch(() => setInitError('Failed to connect to mentor service'));
  }, [submissionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text?: string) => {
    const userMessage = (text ?? input).trim();
    if (!userMessage || !sessionId || loading) return;
    setInput('');
    setLoading(true);

    const tempMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: userMessage,
      retrieved_chunks: [],
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempMsg]);

    try {
      const response = await chatApi.sendMessage(sessionId, userMessage);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        {
          id: `user-${Date.now()}`,
          role: 'user' as const,
          content: userMessage,
          retrieved_chunks: [],
          created_at: new Date().toISOString(),
        },
        response,
      ]);
    } catch {
      const failedMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: '__failed__',
        retrieved_chunks: [],
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, failedMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col flex-1 bg-[#1c1d25] border border-[#2d2e3a] rounded-xl overflow-hidden">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {initError && (
          <div className="text-center py-4 text-red-400 text-sm">{initError}</div>
        )}

        {!initError && messages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-10 gap-4">
            <div className="w-12 h-12 rounded-full bg-brand-900/40 border border-brand-800/50 flex items-center justify-center">
              <svg className="w-6 h-6 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
            </div>
            <div className="text-center">
              <p className="text-[#dddfe4] font-medium mb-1">AI Mentor Ready</p>
              <p className="text-[#7e8088] text-sm">Ask me anything about your submission</p>
            </div>
            <div className="flex flex-col gap-2 w-full max-w-md mt-2">
              {STARTER_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  disabled={!sessionId || loading}
                  className="text-left text-xs text-[#9a9ba8] px-3 py-2 bg-[#13141a] border border-[#3a3b48] rounded-lg hover:border-brand-800 hover:text-[#dddfe4] transition-colors disabled:opacity-40"
                >
                  <span className="text-brand-500 mr-1.5">&#8250;</span>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => {
          const isFailed = msg.role === 'assistant' && msg.content === '__failed__';
          return (
            <div
              key={msg.id || i}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className={`w-6 h-6 flex-shrink-0 rounded-full border flex items-center justify-center mr-2 mt-1 ${isFailed ? 'bg-red-900/30 border-red-800/50' : 'bg-brand-900/50 border-brand-800/50'}`}>
                  <span className={`text-xs ${isFailed ? 'text-red-400' : 'text-brand-400'}`}>AI</span>
                </div>
              )}
              {isFailed ? (
                <div className="max-w-[78%] rounded-xl rounded-bl-sm px-4 py-2.5 text-sm bg-red-900/20 border border-red-800/40 text-red-400 flex items-center gap-2">
                  <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                  </svg>
                  Failed — the mentor model may still be loading. Try again in a moment.
                </div>
              ) : (
                <div
                  className={`max-w-[78%] rounded-xl px-4 py-2.5 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-brand-600 text-white rounded-br-sm'
                      : 'bg-[#252630] border border-[#3a3b48] text-[#dddfe4] rounded-bl-sm'
                  }`}
                >
                  {msg.role === 'assistant' ? renderContent(msg.content) : msg.content}
                </div>
              )}
            </div>
          );
        })}

        {loading && (
          <div className="flex justify-start">
            <div className="w-6 h-6 flex-shrink-0 rounded-full bg-brand-900/50 border border-brand-800/50 flex items-center justify-center mr-2 mt-1">
              <span className="text-brand-400 text-xs">AI</span>
            </div>
            <div className="bg-[#252630] border border-[#3a3b48] rounded-xl rounded-bl-sm px-4 py-3 flex items-center gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-bounce" style={{ animationDelay: '300ms' }} />
              <span className="text-xs text-[#7e8088] ml-1">Loading Mentor...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div className="p-4 border-t border-[#2d2e3a] bg-[#13141a]">
        <div className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask your mentor... (Enter to send, Shift+Enter for newline)"
            disabled={loading || !sessionId}
            className="flex-1 bg-[#1c1d25] border border-[#3a3b48] rounded-lg px-3 py-2.5 text-sm text-[#dddfe4] placeholder-gray-600 focus:outline-none focus:border-brand-700 disabled:opacity-40 resize-none max-h-32 overflow-y-auto"
            style={{ lineHeight: '1.5' }}
          />
          <button
            onClick={() => sendMessage()}
            disabled={loading || !input.trim() || !sessionId}
            className="px-4 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors flex-shrink-0"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
