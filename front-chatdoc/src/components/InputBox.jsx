import styled from 'styled-components';

const Wrapper = styled.div`
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 14px;
  margin-top: 16px;

  @media (max-width: 720px) {
    grid-template-columns: 1fr;
  }
`;

const Textarea = styled.textarea`
  min-height: 110px;
  resize: vertical;
  border: 1px solid rgba(162, 139, 100, 0.34);
  border-radius: 22px;
  padding: 16px 18px;
  background: rgba(255, 255, 255, 0.82);
  color: #17323d;
  outline: none;
  box-shadow: inset 0 1px 2px rgba(71, 62, 45, 0.04);

  &:focus {
    border-color: rgba(29, 103, 116, 0.78);
  }
`;

const Actions = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 10px;
`;

const Hint = styled.div`
  color: #6b7280;
  font-size: 0.88rem;
  line-height: 1.5;
`;

const SendButton = styled.button`
  min-width: 140px;
  border: none;
  border-radius: 18px;
  padding: 14px 16px;
  background: linear-gradient(135deg, #d97706 0%, #c2410c 100%);
  color: #fffdf7;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 16px 26px rgba(194, 65, 12, 0.22);

  &:disabled {
    cursor: not-allowed;
    opacity: 0.55;
    box-shadow: none;
  }
`;

function InputBox({ value, onChange, onSend, disabled, selectedCount }) {
  return (
    <Wrapper>
      <Textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="输入你的问题。比如：这份文档的核心观点是什么？或者：先搜索 MCP，再结合文档写一段简历描述。"
        disabled={disabled}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            onSend();
          }
        }}
      />
      <Actions>
        <Hint>当前已选 {selectedCount} 份文档。按 Enter 发送，Shift + Enter 换行。</Hint>
        <SendButton type="button" onClick={onSend} disabled={disabled || !value.trim()}>
          {disabled ? '处理中...' : '发送问题'}
        </SendButton>
      </Actions>
    </Wrapper>
  );
}

export default InputBox;
