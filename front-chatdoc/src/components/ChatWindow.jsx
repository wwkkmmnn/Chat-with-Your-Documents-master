import { useEffect, useRef } from 'react';
import styled from 'styled-components';

const Wrapper = styled.section`
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 24px;
  background: rgba(255, 252, 246, 0.84);
  border: 1px solid rgba(188, 163, 123, 0.34);
  border-radius: 28px;
  box-shadow: 0 24px 48px rgba(71, 62, 45, 0.1);
  backdrop-filter: blur(14px);
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
  margin-bottom: 18px;
`;

const HeaderTitle = styled.div`
  font-size: 1.2rem;
  font-weight: 800;
  color: #17323d;
`;

const RouteBadge = styled.span`
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(35, 114, 133, 0.12);
  color: #155668;
  font-weight: 700;
  font-size: 0.85rem;
`;

const ScrollArea = styled.div`
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-right: 6px;
`;

const EmptyState = styled.div`
  margin: auto 0;
  padding: 28px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(35, 114, 133, 0.08), rgba(255, 224, 173, 0.32));
  color: #43505d;
  line-height: 1.7;
`;

const MessageCard = styled.article`
  align-self: ${({ $type }) =>
    $type === 'user' ? 'flex-end' : $type === 'assistant' ? 'stretch' : 'center'};
  max-width: ${({ $type }) => ($type === 'assistant' ? '100%' : '82%')};
  padding: 14px 16px;
  border-radius: 22px;
  border: 1px solid
    ${({ $type }) =>
      $type === 'user'
        ? 'rgba(17, 76, 100, 0.16)'
        : $type === 'tool'
          ? 'rgba(191, 160, 118, 0.32)'
          : 'rgba(162, 139, 100, 0.22)'};
  background: ${({ $type }) =>
    $type === 'user'
      ? 'linear-gradient(135deg, #237285, #114c64)'
      : $type === 'tool'
        ? 'rgba(255, 243, 214, 0.88)'
        : 'rgba(255, 255, 255, 0.78)'};
  color: ${({ $type }) => ($type === 'user' ? '#fffdf7' : '#17323d')};
  box-shadow: ${({ $type }) =>
    $type === 'user' ? '0 16px 30px rgba(17, 76, 100, 0.18)' : '0 12px 22px rgba(71, 62, 45, 0.06)'};
`;

const MessageLabel = styled.div`
  margin-bottom: 8px;
  font-size: 0.82rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  opacity: 0.8;
`;

const MessageText = styled.div`
  white-space: pre-wrap;
  line-height: 1.65;
  word-break: break-word;
`;

function messageLabel(message) {
  if (message.type === 'tool') {
    return `工具 · ${message.metadata?.tool || 'tool'}`;
  }
  if (message.role === 'user') {
    return '你';
  }
  return '助手';
}

function ChatWindow({ messages, routeInfo, isStreaming }) {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <Wrapper>
      <Header>
        <HeaderTitle>多工具对话</HeaderTitle>
        <RouteBadge>{isStreaming ? routeInfo?.label || '处理中...' : routeInfo?.label || '待命中'}</RouteBadge>
      </Header>

      <ScrollArea ref={scrollRef}>
        {messages.length === 0 ? (
          <EmptyState>
            上传文档后，你可以直接问“这份 PDF 讲了什么”，也可以问“先搜索 MCP，再结合文档写一段简历描述”。
          </EmptyState>
        ) : (
          messages.map((message) => (
            <MessageCard key={message.id} $type={message.type || message.role}>
              <MessageLabel>{messageLabel(message)}</MessageLabel>
              <MessageText>{message.content || (message.role === 'assistant' && isStreaming ? '...' : '')}</MessageText>
            </MessageCard>
          ))
        )}
      </ScrollArea>
    </Wrapper>
  );
}

export default ChatWindow;
