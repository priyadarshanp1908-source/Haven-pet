import React, { useState, useEffect, useRef } from 'react';
import { usePet } from '../context/PetContext';
import api from '../services/api';
import { Send, Sparkles, Dog, Bot, User, Camera, Stethoscope, HelpCircle, Calendar, ShieldAlert, Utensils, RefreshCw } from 'lucide-react';
import styles from './Chat.module.css';

export default function Chat() {
  const { activePet, pets } = usePet();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');
  const [recognizing, setRecognizing] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, recognizing]);

  const categories = [
    { id: 'all', label: '🌟 Active Pet AI', icon: Sparkles },
    { id: 'health', label: '🩺 Symptom Checker', icon: Stethoscope },
    { id: 'breed', label: '📷 Breed ID', icon: Camera },
  ];

  const quickPrompts = {
    all: [
      `What care routine is best for ${activePet?.name || 'my pet'}?`,
      `Check ${activePet?.name || 'my pet'}'s health and species requirements`,
      `What environmental setup does ${activePet?.name || 'my pet'} need?`,
      `What signs of stress or illness should I watch for in ${activePet?.name || 'my pet'}?`,
    ],
    health: [
      `${activePet?.name || 'My pet'} is feeling lethargic — what should I check?`,
      `What are symptoms requiring an immediate vet visit for ${activePet ? `${activePet.name} (${activePet.species})` : 'my pet'}?`,
      `How to check energy and appetite for ${activePet?.name || 'my pet'}?`,
    ],
    breed: [
      `Upload a photo using the camera button to identify species & breed!`,
      `What are unique characteristics of ${activePet?.breed || 'my pet breed'}?`,
      `How to confirm ${activePet?.name || 'my pet'}'s breed features?`,
    ],
  };

  const handleSend = async (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const res = await api.post('/chat', {
        pet_id: activePet?.id || null,
        message: query,
      });

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: res.data.reply,
        agent_used: res.data.agent_used,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: '⚠️ Sorry, I encountered an error responding to your message. Please try again.',
          agent_used: 'system',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Image Upload for Breed Recognition
  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Local preview URL
    const previewUrl = URL.createObjectURL(file);

    const userImgMsg = {
      id: Date.now().toString(),
      role: 'user',
      content: `Uploaded pet photo for breed identification: ${file.name}`,
      image_url: previewUrl,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userImgMsg]);
    setRecognizing(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await api.post('/ml/recognize', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const result = res.data;
      const formattedReply = (
        `🔍 **AI Breed & Species Recognition Result:**\n\n` +
        `• **Detected Species:** ${result.species ? result.species.toUpperCase() : 'Unknown'}\n` +
        `• **Identified Breed:** **${result.breed || 'Mixed / Unknown'}**\n` +
        `• **Confidence Score:** ${(result.confidence * 100).toFixed(1)}%\n\n` +
        `**Health & Vitality Indicators:**\n` +
        (result.health_tags && result.health_tags.length > 0
          ? result.health_tags.map((t) => `  - ✅ ${t.label.replace('_', ' ')} (${(t.confidence * 100).toFixed(0)}%)`).join('\n')
          : '  - ✅ General healthy appearance detected') +
        `\n\n💬 *${result.message}*`
      );

      const assistantMsg = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: formattedReply,
        agent_used: 'breed_recognition_ai',
        recognition_result: result,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: '⚠️ Failed to analyze image. Please ensure it is a valid image file (JPG, PNG, WebP) and try again.',
          agent_used: 'system',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setRecognizing(false);
      // Reset input value so same file can be selected again
      e.target.value = '';
    }
  };

  // Helper to format response text (supports basic markdown: bold, headers, lists)
  const renderFormattedText = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    return lines.map((line, idx) => {
      let trimmed = line.trim();
      if (!trimmed) return <div key={idx} className={styles.lineSpacer} />;

      // Header 1 (# Header)
      if (trimmed.startsWith('# ')) {
        return <h3 key={idx} className={styles.msgH1}>{trimmed.replace('# ', '')}</h3>;
      }
      // Header 2 (## Header)
      if (trimmed.startsWith('## ')) {
        return <h4 key={idx} className={styles.msgH2}>{trimmed.replace('## ', '')}</h4>;
      }

      // Render inline bold text (**text**)
      const parts = line.split(/(\*\*.*?\*\*)/g);
      const formattedParts = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={pIdx}>{part.slice(2, -2)}</strong>;
        }
        return part;
      });

      // Bullet points
      if (trimmed.startsWith('•') || trimmed.startsWith('-')) {
        return (
          <div key={idx} className={styles.bulletLine}>
            <span className={styles.bulletDot}>•</span>
            <span>{formattedParts}</span>
          </div>
        );
      }

      return <p key={idx} className={styles.msgParagraph}>{formattedParts}</p>;
    });
  };

  const currentPrompts = quickPrompts[activeCategory] || quickPrompts.all;

  return (
    <div className={styles.chatContainer}>
      {/* Chat Header */}
      <div className={styles.chatHeader}>
        <div className={styles.headerInfo}>
          <div className={styles.botBadge}>
            <Bot size={24} />
          </div>
          <div>
            <h2>Haven Pet AI Assistant</h2>
            <p className={styles.petContextText}>
              {activePet ? (
                <>Dedicated Assistant for: <strong>🐾 {activePet.name}</strong> ({activePet.species} — {activePet.breed || 'Mix'})</>
              ) : (
                'Select a pet profile to get tailored AI assistance'
              )}
            </p>
          </div>
        </div>

        {/* Symptom Checker Quick Action Button */}
        <button
          onClick={() => handleSend(`🩺 Help me check ${activePet?.name || 'my pet'}'s health symptoms.`)}
          className={styles.symptomBtn}
          title="Start Health & Symptom Assessment"
        >
          <Stethoscope size={16} /> Symptom Check
        </button>
      </div>

      {/* Category Tabs */}
      <div className={styles.categoryBar}>
        {categories.map((cat) => {
          const Icon = cat.icon;
          return (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`${styles.categoryTab} ${activeCategory === cat.id ? styles.activeTab : ''}`}
            >
              <Icon size={14} />
              <span>{cat.label}</span>
            </button>
          );
        })}
      </div>

      {/* Messages Area */}
      <div className={styles.messagesBox}>
        {messages.length === 0 ? (
          <div className={styles.welcomeBox}>
            <div className={styles.sparkleCircle}>
              <Sparkles size={36} />
            </div>
            <h3>Hello! AI Care Assistant for {activePet ? activePet.name : 'your pet'}</h3>
            <p>
              Ask any health symptom question or get specific advice tailored strictly to{' '}
              <strong>{activePet ? `${activePet.name} (${activePet.species} - ${activePet.breed || 'Mix'})` : 'your active pet profile'}</strong>,
              or upload a photo below to run AI Breed Identification!
            </p>

            <div className={styles.quickPromptsGrid}>
              {currentPrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(prompt)}
                  className={styles.quickPromptBtn}
                >
                  💬 {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`${styles.messageWrapper} ${
                msg.role === 'user' ? styles.userMsg : styles.assistantMsg
              }`}
            >
              <div className={styles.messageAvatar}>
                {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
              </div>
              <div className={styles.messageBubble}>
                {msg.role === 'assistant' && msg.agent_used && (
                  <span className={styles.agentTag}>
                    🤖 {msg.agent_used.replace(/_/g, ' ')}
                  </span>
                )}

                {/* User uploaded image preview */}
                {msg.image_url && (
                  <div className={styles.msgImageContainer}>
                    <img src={msg.image_url} alt="Pet Upload" className={styles.msgImage} />
                  </div>
                )}

                <div className={styles.messageText}>
                  {renderFormattedText(msg.content)}
                </div>

                {/* Recognition health tags badges */}
                {msg.recognition_result?.health_tags && (
                  <div className={styles.tagsRow}>
                    {msg.recognition_result.health_tags.map((tag, i) => (
                      <span key={i} className={styles.healthBadge}>
                        ✨ {tag.label.replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {(loading || recognizing) && (
          <div className={`${styles.messageWrapper} ${styles.assistantMsg}`}>
            <div className={styles.messageAvatar}>
              <Bot size={18} />
            </div>
            <div className={`${styles.messageBubble} ${styles.typingBubble}`}>
              <span className={styles.typingDot} />
              <span className={styles.typingDot} />
              <span className={styles.typingDot} />
              <span className={styles.typingLabel}>
                {recognizing ? 'Analyzing pet photo for species & breed...' : 'Thinking...'}
              </span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className={styles.inputBar}
      >
        {/* Hidden file input for camera/photo upload */}
        <input
          type="file"
          ref={fileInputRef}
          accept="image/*"
          onChange={handleImageUpload}
          style={{ display: 'none' }}
        />

        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className={styles.cameraBtn}
          title="Upload pet photo for Breed Identification"
          disabled={loading || recognizing}
        >
          <Camera size={20} />
        </button>

        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={
            activePet
              ? `Ask anything about ${activePet.name}'s routine, health, or diet...`
              : 'Ask a question or upload a photo for breed ID...'
          }
          className={styles.chatInput}
        />
        <button type="submit" disabled={!input.trim() || loading || recognizing} className={styles.sendBtn}>
          <Send size={18} />
        </button>
      </form>
    </div>
  );
}

