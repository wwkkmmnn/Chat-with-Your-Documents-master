import styled from 'styled-components';

const Sidebar = styled.aside`
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
`;

const Panel = styled.section`
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 18px;
  background: rgba(255, 252, 246, 0.84);
  border: 1px solid rgba(188, 163, 123, 0.34);
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(71, 62, 45, 0.08);
  backdrop-filter: blur(14px);
`;

const Title = styled.h2`
  margin: 0;
  font-size: 0.92rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #7d6240;
`;

const CreateButton = styled.button`
  border: none;
  border-radius: 16px;
  padding: 12px 14px;
  background: linear-gradient(135deg, #237285 0%, #114c64 100%);
  color: #fffdf7;
  font-weight: 700;
  cursor: pointer;

  &:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
`;

const SessionList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
  min-height: 0;
`;

const SessionButton = styled.button`
  text-align: left;
  border: 1px solid ${({ $active }) => ($active ? '#1d6774' : 'rgba(162, 139, 100, 0.28)')};
  background: ${({ $active }) =>
    $active
      ? 'linear-gradient(135deg, rgba(35, 114, 133, 0.18), rgba(255, 232, 194, 0.72))'
      : 'rgba(255, 255, 255, 0.74)'};
  border-radius: 18px;
  padding: 12px 14px;
  cursor: pointer;
  color: #17323d;
`;

const SessionTitle = styled.div`
  font-weight: 700;
  margin-bottom: 6px;
`;

const SessionMeta = styled.div`
  font-size: 0.82rem;
  color: #6b7280;
`;

const EmptyText = styled.p`
  margin: 0;
  color: #6b7280;
  line-height: 1.5;
`;

function formatTime(value) {
  if (!value) {
    return '刚刚';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function SessionSidebar({ sessions, activeSessionId, onCreateSession, onSelectSession, disabled }) {
  return (
    <Sidebar>
      <Panel>
        <Title>会话管理</Title>
        <CreateButton type="button" onClick={onCreateSession} disabled={disabled}>
          新建会话
        </CreateButton>
        <SessionList>
          {sessions.length === 0 ? (
            <EmptyText>会话列表还是空的。新建一个对话后，就可以开始文档问答和工具调用。</EmptyText>
          ) : (
            sessions.map((session) => (
              <SessionButton
                key={session.id}
                type="button"
                $active={session.id === activeSessionId}
                onClick={() => onSelectSession(session.id)}
                disabled={disabled}
              >
                <SessionTitle>{session.title || '未命名会话'}</SessionTitle>
                <SessionMeta>
                  {session.messageCount} 条消息 · 更新于 {formatTime(session.updatedAt)}
                </SessionMeta>
              </SessionButton>
            ))
          )}
        </SessionList>
      </Panel>
    </Sidebar>
  );
}

export default SessionSidebar;
