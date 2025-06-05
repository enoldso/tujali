import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Card, ListGroup, Form, Button, Badge } from 'react-bootstrap';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { messagesAPI } from '../services/api';

interface Conversation {
  patient_id: string;
  patient_name: string;
  last_message: string;
  last_message_time: string;
  unread_count: number;
}

interface Message {
  id: string;
  content: string;
  sender_type: string;
  is_read: boolean;
  created_at: string;
}

const Messages: React.FC = () => {
  const { patientId } = useParams<{ patientId?: string }>();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversation, setActiveConversation] = useState<string | null>(patientId || null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [sending, setSending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Fetch conversations when component mounts
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        setLoading(true);
        const response = await messagesAPI.getConversations();
        setConversations(response.data);
        
        // If no patientId in URL but we have conversations, select the first one
        if (!patientId && response.data.length > 0 && !activeConversation) {
          setActiveConversation(response.data[0].patient_id);
          navigate(`/messages/${response.data[0].patient_id}`, { replace: true });
        }
      } catch (err) {
        console.error('Error fetching conversations:', err);
        setError('Failed to load conversations');
      } finally {
        setLoading(false);
      }
    };
    
    fetchConversations();
  }, [patientId, navigate, activeConversation]);
  
  // Fetch messages when active conversation changes
  useEffect(() => {
    const fetchMessages = async () => {
      if (!activeConversation) return;
      
      try {
        setLoading(true);
        const response = await messagesAPI.getConversation(activeConversation);
        setMessages(response.data);
        
        // Mark messages as read
        messagesAPI.markAsRead(activeConversation);
        
        // Update unread count in conversations list
        setConversations(prevConversations => 
          prevConversations.map(conv => 
            conv.patient_id === activeConversation 
              ? { ...conv, unread_count: 0 } 
              : conv
          )
        );
      } catch (err) {
        console.error('Error fetching messages:', err);
        setError('Failed to load messages');
      } finally {
        setLoading(false);
      }
    };
    
    fetchMessages();
  }, [activeConversation]);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Handle conversation change
  const handleConversationClick = (patientId: string) => {
    setActiveConversation(patientId);
    navigate(`/messages/${patientId}`);
  };
  
  // Handle sending a new message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !activeConversation) return;
    
    try {
      setSending(true);
      await messagesAPI.sendMessage(activeConversation, newMessage);
      
      // Add the new message to the messages list
      const newMsg: Message = {
        id: Date.now().toString(), // Temporary ID
        content: newMessage,
        sender_type: 'provider',
        is_read: true,
        created_at: new Date().toISOString()
      };
      
      setMessages(prevMessages => [...prevMessages, newMsg]);
      setNewMessage('');
      
      // Update the conversations list
      setConversations(prevConversations => 
        prevConversations.map(conv => 
          conv.patient_id === activeConversation 
            ? { 
                ...conv, 
                last_message: newMessage,
                last_message_time: new Date().toISOString()
              } 
            : conv
        )
      );
    } catch (err) {
      console.error('Error sending message:', err);
      alert('Failed to send message');
    } finally {
      setSending(false);
    }
  };
  
  // Format date
  const formatDate = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };
  
  // Format time
  const formatTime = (dateString: string) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  if (loading && !activeConversation) {
    return <div className="text-center p-5">Loading conversations...</div>;
  }
  
  return (
    <Container>
      <h1 className="mb-4">Messages</h1>
      
      <Row>
        {/* Conversations List */}
        <Col md={4} lg={3} className="mb-4 mb-md-0">
          <Card className="shadow-sm h-100">
            <Card.Header>
              <h5 className="mb-0">Conversations</h5>
            </Card.Header>
            <div className="overflow-auto" style={{ maxHeight: 'calc(80vh - 120px)' }}>
              {conversations.length > 0 ? (
                <ListGroup variant="flush">
                  {conversations.map((conversation) => (
                    <ListGroup.Item 
                      key={conversation.patient_id}
                      action
                      active={activeConversation === conversation.patient_id}
                      onClick={() => handleConversationClick(conversation.patient_id)}
                      className="d-flex justify-content-between align-items-start"
                    >
                      <div className="ms-2 me-auto">
                        <div className="fw-bold">{conversation.patient_name}</div>
                        <small 
                          className={
                            conversation.unread_count > 0 ? 'fw-bold' : 'text-muted'
                          }
                        >
                          {conversation.last_message.length > 25
                            ? conversation.last_message.substring(0, 25) + '...'
                            : conversation.last_message}
                        </small>
                      </div>
                      <div className="d-flex flex-column align-items-end">
                        <small className="text-muted">
                          {formatDate(conversation.last_message_time)}
                        </small>
                        {conversation.unread_count > 0 && (
                          <Badge bg="primary" pill>
                            {conversation.unread_count}
                          </Badge>
                        )}
                      </div>
                    </ListGroup.Item>
                  ))}
                </ListGroup>
              ) : (
                <div className="p-3 text-center text-muted">
                  No conversations yet
                </div>
              )}
            </div>
          </Card>
        </Col>
        
        {/* Message Chat */}
        <Col md={8} lg={9}>
          <Card className="shadow-sm h-100">
            {activeConversation ? (
              <>
                <Card.Header className="d-flex justify-content-between align-items-center">
                  <h5 className="mb-0">
                    {conversations.find(c => c.patient_id === activeConversation)?.patient_name}
                  </h5>
                  <Link 
                    to={`/patients/${activeConversation}`} 
                    className="btn btn-sm btn-outline-primary"
                  >
                    View Patient Profile
                  </Link>
                </Card.Header>
                
                <div 
                  className="overflow-auto p-3" 
                  style={{ maxHeight: 'calc(80vh - 230px)' }}
                >
                  {messages.length > 0 ? (
                    <div className="message-list">
                      {messages.map((message) => (
                        <div 
                          key={message.id} 
                          className={`message-bubble ${
                            message.sender_type === 'provider' 
                              ? 'message-from-provider' 
                              : 'message-from-patient'
                          }`}
                        >
                          <div>{message.content}</div>
                          <div className="message-time">
                            {formatTime(message.created_at)}
                          </div>
                        </div>
                      ))}
                      <div ref={messagesEndRef} />
                    </div>
                  ) : (
                    <div className="text-center text-muted p-5">
                      No messages in this conversation yet
                    </div>
                  )}
                </div>
                
                <Card.Footer>
                  <Form onSubmit={handleSendMessage}>
                    <div className="d-flex">
                      <Form.Control
                        type="text"
                        placeholder="Type your message..."
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        disabled={sending}
                      />
                      <Button 
                        type="submit" 
                        variant="primary" 
                        className="ms-2" 
                        disabled={!newMessage.trim() || sending}
                      >
                        {sending ? 'Sending...' : 'Send'}
                      </Button>
                    </div>
                  </Form>
                </Card.Footer>
              </>
            ) : (
              <Card.Body className="d-flex align-items-center justify-content-center">
                <div className="text-center text-muted p-5">
                  <p>Select a conversation to start messaging</p>
                  {conversations.length === 0 && !loading && (
                    <p>No conversations available</p>
                  )}
                </div>
              </Card.Body>
            )}
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Messages;