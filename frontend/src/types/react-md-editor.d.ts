declare module '@uiw/react-md-editor' {
  import * as React from 'react';

  interface MDEditorProps {
    value?: string;
    onChange?: (value?: string) => void;
    height?: number | string;
    textareaProps?: React.TextareaHTMLAttributes<HTMLTextAreaElement>;
    hideToolbar?: boolean;
    visibleDragbar?: boolean;
    preview?: 'live' | 'edit' | 'preview';
    tabIndex?: number;
    [key: string]: any;
  }

  const MDEditor: React.FC<MDEditorProps>;
  export default MDEditor;
}
