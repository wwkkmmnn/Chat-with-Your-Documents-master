import { useDropzone } from 'react-dropzone';
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

const DropArea = styled.div`
  border: 1.5px dashed ${({ $active }) => ($active ? '#1d6774' : 'rgba(125, 98, 64, 0.35)')};
  background: ${({ $active }) =>
    $active ? 'rgba(35, 114, 133, 0.08)' : 'linear-gradient(180deg, rgba(255,255,255,0.76), rgba(250, 241, 227, 0.6))'};
  border-radius: 20px;
  padding: 20px 16px;
  text-align: center;
  color: #4b5563;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;

  &:hover {
    transform: translateY(-1px);
  }
`;

const Hint = styled.p`
  margin: 0;
  line-height: 1.55;
`;

const FileList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const FileCard = styled.label`
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 14px;
  border: 1px solid ${({ $selected }) => ($selected ? '#1d6774' : 'rgba(162, 139, 100, 0.28)')};
  border-radius: 18px;
  background: ${({ $selected }) =>
    $selected ? 'rgba(35, 114, 133, 0.08)' : 'rgba(255, 255, 255, 0.72)'};
  cursor: pointer;
`;

const FileName = styled.div`
  font-weight: 700;
  color: #17323d;
`;

const FileMeta = styled.div`
  margin-top: 4px;
  color: #6b7280;
  font-size: 0.82rem;
  line-height: 1.45;
`;

const EmptyState = styled.p`
  margin: 0;
  color: #6b7280;
  line-height: 1.5;
`;

function formatUploadedAt(value) {
  if (!value) {
    return '刚刚上传';
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

function UploadPanel({ files, selectedFileIds, onUpload, onToggleFile, isUploading, disabled }) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    multiple: false,
    disabled: disabled || isUploading,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    onDrop: (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (file) {
        onUpload(file);
      }
    },
  });

  return (
    <Panel>
      <Title>文档工作区</Title>
      <DropArea {...getRootProps()} $active={isDragActive}>
        <input {...getInputProps()} />
        <Hint>
          {isUploading
            ? '正在上传并建立索引，请稍候...'
            : isDragActive
              ? '把文件放到这里即可建立新的知识库入口。'
              : '拖拽或点击上传 PDF、TXT、DOCX。MVP 重点仍然是 PDF 文档问答。'}
        </Hint>
      </DropArea>

      <FileList>
        {files.length === 0 ? (
          <EmptyState>还没有可检索的文档。先上传一份 PDF，再开始问答。</EmptyState>
        ) : (
          files.map((file) => {
            const selected = selectedFileIds.includes(file.id);
            return (
              <FileCard key={file.id} $selected={selected}>
                <input
                  type="checkbox"
                  checked={selected}
                  onChange={() => onToggleFile(file.id)}
                  disabled={disabled || isUploading}
                />
                <div>
                  <FileName>{file.name}</FileName>
                  <FileMeta>
                    {file.chunkCount} 个片段 · {file.pageCount} 页/段 · 上传于 {formatUploadedAt(file.uploadedAt)}
                  </FileMeta>
                </div>
              </FileCard>
            );
          })
        )}
      </FileList>
    </Panel>
  );
}

export default UploadPanel;
