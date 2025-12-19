import React, { useState, useEffect } from 'react';
import { Card, Table, Switch, Button, message, Spin, Tag, Space, Modal, Descriptions } from 'antd';
import { InfoCircleOutlined, ReloadOutlined, EyeOutlined, SettingOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import axios from 'axios';
import { useApplication } from '../../contexts/ApplicationContext';

// MCP Technique interface (replaces Scanner)
interface Technique {
  technique_id: string;
  name: string;
  description?: string;
  tactic: string;
  severity: string;
  enabled: boolean;
  detection_methods: string[];
  total_detections: number;
  true_positives: number;
  false_positives: number;
}

const OfficialScannersManagement: React.FC = () => {
  const { t } = useTranslation();
  const { currentApplicationId } = useApplication();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [techniques, setTechniques] = useState<Technique[]>([]);
  const [selectedTechnique, setSelectedTechnique] = useState<Technique | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);

  useEffect(() => {
    loadTechniques();
  }, [currentApplicationId]);

  const loadTechniques = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/techniques');
      setTechniques(response.data.techniques || []);
    } catch (error) {
      message.error(t('scannerPackages.loadFailed') || 'Failed to load techniques');
      console.error('Failed to load techniques:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (techniqueId: string, enabled: boolean) => {
    try {
      setSaving(true);
      await axios.patch(`/api/v1/techniques/${techniqueId}`, { enabled });
      message.success(t('scannerPackages.configurationSaved') || 'Configuration saved');
      setTechniques(prev => prev.map(t =>
        t.technique_id === techniqueId ? { ...t, enabled } : t
      ));
    } catch (error) {
      message.error(t('scannerPackages.updateFailed') || 'Update failed');
      console.error('Failed to update technique:', error);
    } finally {
      setSaving(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    const colors: Record<string, string> = {
      CRITICAL: 'red',
      HIGH: 'orange',
      MEDIUM: 'gold',
      LOW: 'blue',
    };
    return colors[severity] || 'default';
  };

  const columns = [
    {
      title: t('scannerPackages.scannerId') || 'Technique ID',
      dataIndex: 'technique_id',
      key: 'technique_id',
      width: 150,
      render: (id: string) => <Tag color="blue">{id}</Tag>,
    },
    {
      title: t('scannerPackages.name') || 'Name',
      dataIndex: 'name',
      key: 'name',
      width: 300,
    },
    {
      title: t('scannerPackages.type') || 'Tactic',
      dataIndex: 'tactic',
      key: 'tactic',
      width: 150,
      render: (tactic: string) => <Tag>{tactic}</Tag>,
    },
    {
      title: t('scannerPackages.riskLevel') || 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 120,
      render: (severity: string) => (
        <Tag color={getSeverityColor(severity)}>{severity}</Tag>
      ),
    },
    {
      title: 'Detection Methods',
      dataIndex: 'detection_methods',
      key: 'detection_methods',
      width: 200,
      render: (methods: string[]) => (
        <Space size={[0, 4]} wrap>
          {methods?.map((method, index) => (
            <Tag key={index} color="green">
              {method}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: t('scannerPackages.detections') || 'Detections',
      dataIndex: 'total_detections',
      key: 'total_detections',
      width: 100,
      align: 'center' as const,
    },
    {
      title: 'Accuracy',
      key: 'accuracy',
      width: 100,
      align: 'center' as const,
      render: (_: any, record: Technique) => {
        const total = record.true_positives + record.false_positives;
        const accuracy = total > 0 ? ((record.true_positives / total) * 100).toFixed(1) : 'N/A';
        return accuracy !== 'N/A' ? `${accuracy}%` : 'N/A';
      },
    },
    {
      title: t('scannerPackages.status') || 'Status',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (enabled: boolean, record: Technique) => (
        <Switch
          checked={enabled}
          onChange={(checked) => handleToggle(record.technique_id, checked)}
          disabled={saving}
        />
      ),
    },
    {
      title: t('scannerPackages.actions') || 'Actions',
      key: 'actions',
      width: 150,
      render: (_: any, record: Technique) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => {
            setSelectedTechnique(record);
            setDetailVisible(true);
          }}
        >
          {t('scannerPackages.details') || 'Details'}
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          {t('scannerPackages.officialScanners') || 'SAFE-MCP Techniques'}
        </Space>
      }
      extra={
        <Button icon={<ReloadOutlined />} onClick={loadTechniques}>
          {t('scannerPackages.refresh') || 'Refresh'}
        </Button>
      }
    >
      <Table
        columns={columns}
        dataSource={techniques}
        loading={loading}
        rowKey="technique_id"
        pagination={{
          pageSize: 20,
          showTotal: (total) => `${t('scannerPackages.total') || 'Total'} ${total} ${t('scannerPackages.techniques') || 'techniques'}`,
        }}
      />

      <Modal
        title={`${t('scannerPackages.techniqueDetails') || 'Technique Details'}: ${selectedTechnique?.technique_id}`}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTechnique && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label={t('scannerPackages.techniqueId') || 'Technique ID'}>
              {selectedTechnique.technique_id}
            </Descriptions.Item>
            <Descriptions.Item label={t('scannerPackages.name') || 'Name'}>
              {selectedTechnique.name}
            </Descriptions.Item>
            <Descriptions.Item label={t('scannerPackages.tactic') || 'Tactic'}>
              <Tag>{selectedTechnique.tactic}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label={t('scannerPackages.severity') || 'Severity'}>
              <Tag color={getSeverityColor(selectedTechnique.severity)}>
                {selectedTechnique.severity}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label={t('scannerPackages.description') || 'Description'}>
              {selectedTechnique.description || 'No description available'}
            </Descriptions.Item>
            <Descriptions.Item label="Detection Methods">
              <Space size={[0, 8]} wrap>
                {selectedTechnique.detection_methods?.map((method, index) => (
                  <Tag key={index} color="green">
                    {method}
                  </Tag>
                ))}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="Statistics">
              <Space direction="vertical">
                <div>Total Detections: {selectedTechnique.total_detections}</div>
                <div>True Positives: {selectedTechnique.true_positives}</div>
                <div>False Positives: {selectedTechnique.false_positives}</div>
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label={t('scannerPackages.status') || 'Status'}>
              <Switch
                checked={selectedTechnique.enabled}
                onChange={(checked) =>
                  handleToggle(selectedTechnique.technique_id, checked)
                }
              />
              {selectedTechnique.enabled ? ' Enabled' : ' Disabled'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </Card>
  );
};

export default OfficialScannersManagement;
