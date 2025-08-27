import React from 'react';
import { Layout, Typography } from 'antd';

const { Footer } = Layout;
const { Text } = Typography;

const AppFooter: React.FC = () => {
  return (
    <Footer className="app-footer">
      <Text type="secondary">
        © 2024 RedFire 量化交易平台. All rights reserved.
      </Text>
    </Footer>
  );
};

export default AppFooter;
