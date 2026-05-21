import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService } from './chat.service';
import { ChatMessage, ChatTrace } from './models/chat-message';

interface ChatSession {
  localId: string;
  conversationId: string;
  title: string;
  updatedAt: string;
  messages: ChatMessage[];
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'Open Chatbot By Mandar';
  messages: ChatMessage[] = [];
  sessions: ChatSession[] = [];
  activeSessionId = '';
  inputText = '';
  conversationId = '';
  isSending = false;
  statusMessage = 'Ready';
  isFeatureMenuOpen = false;

  readonly suggestedPrompts = [
    'Summarize this conversation',
    'Find revenue trends from uploaded data',
    'Draft a customer email',
    'Explain the agent trace'
  ];

  constructor(private chatService: ChatService) {}

  sendMessage(): void {
    const trimmed = this.inputText.trim();
    if (!trimmed || this.isSending) {
      return;
    }

    const session = this.ensureActiveSession(trimmed);
    this.isSending = true;
    this.statusMessage = 'Thinking';
    this.isFeatureMenuOpen = false;

    const userMessage: ChatMessage = {
      role: 'user',
      content: trimmed,
      timestamp: new Date().toISOString()
    };

    this.messages = [...this.messages, userMessage];
    session.messages = [...this.messages];
    session.updatedAt = userMessage.timestamp;
    this.inputText = '';

    this.chatService.sendMessage({
      message: trimmed,
      conversation_id: this.conversationId || undefined
    }).subscribe({
      next: response => {
        this.conversationId = response.conversation_id;
        session.conversationId = response.conversation_id;

        const assistantMessage: ChatMessage = {
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toISOString(),
          metadata: response.metadata
        };

        this.messages = [...this.messages, assistantMessage];
        session.messages = [...this.messages];
        session.updatedAt = assistantMessage.timestamp;
        this.bumpSession(session.localId);
        this.statusMessage = response.metadata?.trace?.summary?.selected_capability
          ? this.formatLabel(response.metadata.trace.summary.selected_capability)
          : 'Answered';
        this.isSending = false;
        setTimeout(() => this.scrollToBottom(), 50);
      },
      error: error => {
        const errorText = error?.error?.detail || error.message || 'Unknown error';
        this.statusMessage = `Error: ${errorText}`;
        this.isSending = false;
      }
    });
  }

  startNewChat(): void {
    this.messages = [];
    this.activeSessionId = '';
    this.conversationId = '';
    this.inputText = '';
    this.statusMessage = 'New chat';
    this.isFeatureMenuOpen = false;
  }

  selectSession(session: ChatSession): void {
    this.activeSessionId = session.localId;
    this.conversationId = session.conversationId;
    this.messages = [...session.messages];
    this.statusMessage = 'Ready';
    this.isFeatureMenuOpen = false;
    setTimeout(() => this.scrollToBottom(), 50);
  }

  clearConversation(): void {
    this.startNewChat();
  }

  useSuggestedPrompt(prompt: string): void {
    this.inputText = prompt;
  }

  toggleFeatureMenu(): void {
    this.isFeatureMenuOpen = !this.isFeatureMenuOpen;
  }

  closeFeatureMenu(): void {
    this.isFeatureMenuOpen = false;
  }

  private ensureActiveSession(firstMessage: string): ChatSession {
    const existing = this.sessions.find(session => session.localId === this.activeSessionId);
    if (existing) {
      return existing;
    }

    const now = new Date().toISOString();
    const session: ChatSession = {
      localId: `local-${Date.now()}`,
      conversationId: '',
      title: this.makeTitle(firstMessage),
      updatedAt: now,
      messages: []
    };

    this.sessions = [session, ...this.sessions];
    this.activeSessionId = session.localId;
    return session;
  }

  private bumpSession(localId: string): void {
    const session = this.sessions.find(item => item.localId === localId);
    if (!session) {
      return;
    }

    this.sessions = [
      session,
      ...this.sessions.filter(item => item.localId !== localId)
    ];
  }

  private makeTitle(message: string): string {
    const normalized = message.replace(/\s+/g, ' ').trim();
    return normalized.length > 42 ? `${normalized.slice(0, 42)}...` : normalized;
  }

  private scrollToBottom(): void {
    const container = document.querySelector('.conversation');
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  }

  formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  formatSessionTime(timestamp: string): string {
    return new Date(timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' });
  }

  getTrace(message: ChatMessage): ChatTrace | undefined {
    return message.metadata?.trace;
  }

  formatLabel(value?: string): string {
    if (!value) {
      return 'Not available';
    }

    return value
      .replace(/_/g, ' ')
      .replace(/\b\w/g, char => char.toUpperCase());
  }

  formatConfidence(value?: number): string {
    if (value === undefined || value === null) {
      return 'N/A';
    }

    return `${Math.round(value * 100)}%`;
  }

  formatDuration(value?: number): string {
    if (value === undefined || value === null) {
      return 'N/A';
    }

    return `${value} ms`;
  }
}
