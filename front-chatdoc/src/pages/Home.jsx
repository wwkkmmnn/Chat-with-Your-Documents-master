import { startTransition, useEffect, useRef, useState } from 'react';
import styled from 'styled-components';

import { streamChat } from '../api/chat';
import { createSession, fetchSessionMessages, fetchSessions } from '../api/session';
import { fetchFiles, uploadDocument } from '../api/upload';
import ChatWindow from '../components/ChatWindow';
import InputBox from '../components/InputBox';
import SessionSidebar from '../components/SessionSidebar';
import ToolCallPanel from '../components/ToolCallPanel';
import UploadPanel from '../components/UploadPanel';

const Page = styled.main`
  min-height: 100vh;
  padding: 28px;

  @media (max-width: 720px) {
    padding: 16px;
  }
`;

const Hero = styled.header`
  margin-bottom: 20px;
  padding: 22px 24px;
  border-radius: 28px;
  border: 1px solid rgba(188, 163, 123, 0.28);
  background:
    radial-gradient(circle at right top, rgba(255, 214, 138, 0.28), transparent 28%),
    linear-gradient(135deg, rgba(255, 251, 245, 0.88), rgba(252, 240, 220, 0.76));
  box-shadow: 0 26px 50px rgba(71, 62, 45, 0.1);
`;

const Eyebrow = styled.div`
  margin-bottom: 8px;
  color: #8a6642;
  font-size: 0.84rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
`;

const Title = styled.h1`
  margin: 0;
  font-size: clamp(2rem, 4vw, 3.2rem);
  line-height: 1.05;
  color: #17323d;
`;

const Subtitle = styled.p`
  margin: 10px 0 0;
  max-width: 880px;
  color: #4b5563;
  line-height: 1.65;
  font-size: 1rem;
`;

const ErrorBanner = styled.div`
  margin-bottom: 18px;
  padding: 14px 16px;
  border-radius: 18px;
  border: 1px solid rgba(220, 38, 38, 0.18);
  background: rgba(254, 226, 226, 0.82);
  color: #991b1b;
  line-height: 1.55;
`;

const Layout = styled.section`
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr) 340px;
  gap: 18px;
  align-items: start;

  @media (max-width: 1280px) {
    grid-template-columns: 260px minmax(0, 1fr);
  }

  @media (max-width: 1080px) {
    grid-template-columns: 1fr;
  }
`;

const CenterColumn = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 78vh;
`;

const RightColumn = styled.div`
  display: flex;
  flex-direction: column;
  gap: 18px;

  @media (max-width: 1280px) {
    grid-column: span 2;
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  @media (max-width: 1080px) {
    grid-column: auto;
    grid-template-columns: 1fr;
  }
`;

function localMessage({ id, role, type, content, metadata = {} }) {
  return {
    id,
    role,
    type,
    content,
    metadata,
    createdAt: new Date().toISOString(),
  };
}

function upsertToolCall(previousCalls, payload) {
  const existingIndex = previousCalls.findIndex((item) => item.tool === payload.tool);
  const nextCall = {
    id: existingIndex >= 0 ? previousCalls[existingIndex].id : `tool_${payload.tool}`,
    tool: payload.tool,
    label: payload.label || payload.tool,
    status: payload.status || 'running',
    summary: payload.summary || '',
    items: payload.items || [],
  };

  if (existingIndex >= 0) {
    return previousCalls.map((item, index) => (index === existingIndex ? nextCall : item));
  }

  return [nextCall, ...previousCalls];
}

function Home() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState('');
  const [messages, setMessages] = useState([]);
  const [files, setFiles] = useState([]);
  const [selectedFileIds, setSelectedFileIds] = useState([]);
  const [toolCalls, setToolCalls] = useState([]);
  const [routeInfo, setRouteInfo] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isBooting, setIsBooting] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const assistantMessageIdRef = useRef(null);

  useEffect(() => {
    let ignore = false;

    async function bootstrap() {
      try {
        const [sessionPayload, filePayload] = await Promise.all([fetchSessions(), fetchFiles()]);
        if (ignore) {
          return;
        }

        const nextFiles = filePayload.files ?? [];
        let nextSessions = sessionPayload.sessions ?? [];

        if (!nextSessions.length) {
          const created = await createSession();
          if (ignore) {
            return;
          }
          nextSessions = [created.session];
        }

        startTransition(() => {
          setFiles(nextFiles);
          setSessions(nextSessions);
          setSelectedFileIds(nextFiles.slice(0, 1).map((file) => file.id));
        });

        if (nextSessions[0]) {
          const sessionDetail = await fetchSessionMessages(nextSessions[0].id);
          if (ignore) {
            return;
          }
          startTransition(() => {
            setActiveSessionId(nextSessions[0].id);
            setMessages(sessionDetail.messages ?? []);
          });
        }
      } catch (error) {
        if (!ignore) {
          setErrorMessage(error instanceof Error ? error.message : '初始化失败。');
        }
      } finally {
        if (!ignore) {
          setIsBooting(false);
        }
      }
    }

    bootstrap();

    return () => {
      ignore = true;
    };
  }, []);

  async function reloadSessions() {
    const payload = await fetchSessions();
    setSessions(payload.sessions ?? []);
    return payload.sessions ?? [];
  }

  async function reloadFiles() {
    const payload = await fetchFiles();
    setFiles(payload.files ?? []);
    return payload.files ?? [];
  }

  async function loadSession(sessionId) {
    if (!sessionId || isStreaming) {
      return;
    }

    const payload = await fetchSessionMessages(sessionId);
    assistantMessageIdRef.current = null;
    setActiveSessionId(sessionId);
    setMessages(payload.messages ?? []);
    setRouteInfo(null);
    setToolCalls([]);
    setErrorMessage('');
  }

  async function handleCreateSession() {
    if (isStreaming) {
      return;
    }

    try {
      const payload = await createSession();
      assistantMessageIdRef.current = null;
      setSessions((previous) => [payload.session, ...previous]);
      setActiveSessionId(payload.session.id);
      setMessages([]);
      setRouteInfo(null);
      setToolCalls([]);
      setErrorMessage('');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '创建会话失败。');
    }
  }

  async function handleUpload(file) {
    setIsUploading(true);
    try {
      const payload = await uploadDocument(file);
      const nextFiles = await reloadFiles();
      setSelectedFileIds((previous) => {
        const merged = new Set(previous);
        merged.add(payload.file.id);
        return nextFiles.filter((item) => merged.has(item.id)).map((item) => item.id);
      });
      setErrorMessage('');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : '上传失败。');
    } finally {
      setIsUploading(false);
    }
  }

  function handleToggleFile(fileId) {
    setSelectedFileIds((previous) =>
      previous.includes(fileId)
        ? previous.filter((item) => item !== fileId)
        : [...previous, fileId],
    );
  }

  function ensureAssistantMessage(tokenText) {
    setMessages((previous) => {
      if (!assistantMessageIdRef.current) {
        assistantMessageIdRef.current = `assistant_${Date.now()}`;
        return [
          ...previous,
          localMessage({
            id: assistantMessageIdRef.current,
            role: 'assistant',
            type: 'assistant',
            content: tokenText,
          }),
        ];
      }

      return previous.map((message) =>
        message.id === assistantMessageIdRef.current
          ? { ...message, content: `${message.content}${tokenText}` }
          : message,
      );
    });
  }
  {/*处理后端 SSE 流事件的函数，根据事件类型更新路由信息、工具调用状态、消息列表等，确保助手消息正确拼接和更新*/}
  function handleStreamEvent(event) {
    if (event.type === 'route') {
      setRouteInfo(event.data);
      return;
    }

    if (event.type === 'tool_start') {
      setToolCalls((previous) => upsertToolCall(previous, event.data));
      return;
    }

    if (event.type === 'tool_result') {
      setToolCalls((previous) => upsertToolCall(previous, event.data));
      setMessages((previous) => [
        ...previous,
        localMessage({
          id: `tool_${event.data.tool}_${Date.now()}`,
          role: 'tool',
          type: 'tool',
          content: event.data.summary || `${event.data.label || event.data.tool} 已完成。`,
          metadata: {
            tool: event.data.tool,
            items: event.data.items || [],
          },
        }),
      ]);
      return;
    }

    if (event.type === 'token') {
      ensureAssistantMessage(event.data.text || '');
      return;
    }

    if (event.type === 'done' && event.data.sessionId) {
      setActiveSessionId(event.data.sessionId);
    }
  }

  async function handleSend() {
    const message = inputValue.trim();
    if (!message || isStreaming || isBooting) {
      return;
    }

    let sessionId = activeSessionId;

    try {
      if (!sessionId) {
        const created = await createSession();
        sessionId = created.session.id;
        setSessions((previous) => [created.session, ...previous]);
        setActiveSessionId(sessionId);
      }

      setMessages((previous) => [
        ...previous,
        localMessage({
          id: `user_${Date.now()}`,
          role: 'user',
          type: 'user',
          content: message,
        }),
      ]);
      setInputValue('');
      setRouteInfo(null);
      setToolCalls([]);
      setErrorMessage('');
      assistantMessageIdRef.current = null;
      setIsStreaming(true);

      await streamChat(
        {
          sessionId,
          message,
          fileIds: selectedFileIds,
        },
        { onEvent: handleStreamEvent },
      );

      const [sessionDetail] = await Promise.all([fetchSessionMessages(sessionId), reloadSessions()]);
      startTransition(() => {
        setMessages(sessionDetail.messages ?? []);
      });
    } catch (error) {
      const nextError = error instanceof Error ? error.message : '对话失败。';
      setErrorMessage(nextError);
      setMessages((previous) => {
        if (assistantMessageIdRef.current) {
          return previous.map((item) =>
            item.id === assistantMessageIdRef.current
              ? { ...item, content: item.content || nextError }
              : item,
          );
        }

        return [
          ...previous,
          localMessage({
            id: `assistant_error_${Date.now()}`,
            role: 'assistant',
            type: 'assistant',
            content: nextError,
          }),
        ];
      });
    } finally {
      assistantMessageIdRef.current = null;
      setIsStreaming(false);
    }
  }

  return (
    <Page>
      <Hero>
        <Eyebrow>PDF 文档方案重构版</Eyebrow>
        <Title>Multi Tool AI Assistant</Title>
        <Subtitle>
          现在的项目已经从单一 PDF 问答改造成文档检索、网页搜索、统一 Skill 注册表、SSE 流式响应和会话持久化的一体化原型。
        </Subtitle>
      </Hero>

      {errorMessage && <ErrorBanner>{errorMessage}</ErrorBanner>}

      <Layout>
        <SessionSidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onCreateSession={handleCreateSession}
          onSelectSession={loadSession}
          disabled={isStreaming || isBooting}
        />

        <CenterColumn>
          <ChatWindow messages={messages} routeInfo={routeInfo} isStreaming={isStreaming} />
          <InputBox
            value={inputValue}
            onChange={setInputValue}
            onSend={handleSend}
            disabled={isStreaming || isBooting}
            selectedCount={selectedFileIds.length}
          />
        </CenterColumn>

        <RightColumn>
          <UploadPanel
            files={files}
            selectedFileIds={selectedFileIds}
            onUpload={handleUpload}
            onToggleFile={handleToggleFile}
            isUploading={isUploading}
            disabled={isStreaming || isBooting}
          />
          <ToolCallPanel
            routeInfo={routeInfo}
            toolCalls={toolCalls}
            selectedCount={selectedFileIds.length}
          />
        </RightColumn>
      </Layout>
    </Page>
  );
}

export default Home;
