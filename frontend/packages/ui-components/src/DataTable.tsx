import React from 'react';

export interface Column<T = any> {
  title: string;
  dataIndex: string;
  key: string;
  render?: (text: any, record: T, index: number) => React.ReactNode;
  width?: number | string;
  align?: 'left' | 'center' | 'right';
}

export interface DataTableProps<T = any> {
  columns: Column<T>[];
  dataSource: T[];
  loading?: boolean;
  pagination?: {
    current: number;
    pageSize: number;
    total: number;
    onChange: (page: number, pageSize: number) => void;
  } | false;
  className?: string;
  style?: React.CSSProperties;
}

export const DataTable = <T extends Record<string, any> = any>({
  columns,
  dataSource,
  loading = false,
  pagination,
  className,
  style
}: DataTableProps<T>) => {
  const startIndex = pagination && typeof pagination === 'object' ? (pagination.current - 1) * pagination.pageSize : 0;
  const endIndex = pagination && typeof pagination === 'object' ? startIndex + pagination.pageSize : dataSource.length;
  const currentData = pagination && typeof pagination === 'object' ? dataSource.slice(startIndex, endIndex) : dataSource;

  return (
    <div className={`data-table ${className || ''}`} style={style}>
      <table className="data-table-table">
        <thead>
          <tr>
            {columns.map(column => (
              <th 
                key={column.key}
                style={{ 
                  width: column.width,
                  textAlign: column.align || 'left'
                }}
              >
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loading ? (
            <tr>
              <td colSpan={columns.length} style={{ textAlign: 'center', padding: '20px' }}>
                加载中...
              </td>
            </tr>
          ) : currentData.length === 0 ? (
            <tr>
              <td colSpan={columns.length} style={{ textAlign: 'center', padding: '20px' }}>
                暂无数据
              </td>
            </tr>
          ) : (
            currentData.map((record, index) => (
              <tr key={index}>
                {columns.map(column => (
                  <td 
                    key={column.key}
                    style={{ textAlign: column.align || 'left' }}
                  >
                    {column.render 
                      ? column.render(record[column.dataIndex], record, startIndex + index)
                      : record[column.dataIndex]
                    }
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
      
      {pagination && typeof pagination === 'object' && (
        <div className="data-table-pagination">
          <button 
            onClick={() => pagination.onChange(pagination.current - 1, pagination.pageSize)}
            disabled={pagination.current <= 1}
          >
            上一页
          </button>
          <span>
            第 {pagination.current} 页，共 {Math.ceil(pagination.total / pagination.pageSize)} 页
          </span>
          <button 
            onClick={() => pagination.onChange(pagination.current + 1, pagination.pageSize)}
            disabled={pagination.current >= Math.ceil(pagination.total / pagination.pageSize)}
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
};
