import styled from 'styled-components';

const Panel = styled.section`
  display: flex;
  flex-direction: column;
  gap: 14px;
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

const RouteBanner = styled.div`
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(135deg, rgba(35, 114, 133, 0.12), rgba(255, 224, 173, 0.36));
  color: #17323d;
`;

const RouteMode = styled.div`
  font-weight: 800;
  margin-bottom: 4px;
`;

const RouteReason = styled.div`
  color: #5b6470;
  line-height: 1.5;
  font-size: 0.92rem;
`;

const CallList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const CallCard = styled.article`
  border-radius: 18px;
  padding: 14px;
  border: 1px solid rgba(162, 139, 100, 0.28);
  background: rgba(255, 255, 255, 0.72);
`;

const CallHeader = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
`;

const CallTitle = styled.div`
  font-weight: 700;
`;

const Status = styled.span`
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  background: ${({ $status }) =>
    $status === 'running'
      ? 'rgba(245, 158, 11, 0.16)'
      : $status === 'success'
        ? 'rgba(34, 197, 94, 0.16)'
        : 'rgba(107, 114, 128, 0.16)'};
  color: ${({ $status }) =>
    $status === 'running'
      ? '#b45309'
      : $status === 'success'
        ? '#166534'
        : '#4b5563'};
`;

const Summary = styled.p`
  margin: 0;
  color: #4b5563;
  line-height: 1.55;
`;

const ItemList = styled.ul`
  margin: 10px 0 0;
  padding-left: 18px;
  color: #5b6470;
`;

const EmptyState = styled.p`
  margin: 0;
  color: #6b7280;
  line-height: 1.5;
`;

function ToolCallPanel({ routeInfo, toolCalls, selectedCount }) {
  return (
    <Panel>
      <Title>工具状态</Title>
      <RouteBanner>
        <RouteMode>{routeInfo?.label || '等待路由判断'}</RouteMode>
        <RouteReason>
          {routeInfo?.reason || `当前已选择 ${selectedCount} 份文档。发送问题后，这里会展示 route / tool_start / tool_result 事件。`}
        </RouteReason>
      </RouteBanner>

      <CallList>
        {toolCalls.length === 0 ? (
          <EmptyState>本轮还没有触发工具调用。直接问答场景会跳过工具链。</EmptyState>
        ) : (
          toolCalls.map((toolCall) => (
            <CallCard key={toolCall.id}>
              <CallHeader>
                <CallTitle>{toolCall.label || toolCall.tool}</CallTitle>
                <Status $status={toolCall.status}>{toolCall.status}</Status>
              </CallHeader>
              <Summary>{toolCall.summary || '工具已触发，等待返回结果。'}</Summary>
              {!!toolCall.items?.length && (
                <ItemList>
                  {toolCall.items.slice(0, 2).map((item, index) => (
                    <li key={`${toolCall.id}_${index}`}>
                      {item.fileName || item.title || item.source || '结果'} {item.page ? `· 第 ${item.page} 页` : ''}
                    </li>
                  ))}
                </ItemList>
              )}
            </CallCard>
          ))
        )}
      </CallList>
    </Panel>
  );
}

export default ToolCallPanel;
