// 测试系统初始化
require('dotenv').config()

async function testSystems() {
  console.log('开始测试系统...\n')

  // 测试数据库
  console.log('1. 测试数据库连接...')
  try {
    const db = require('./src/memory/database')
    await db.init()
    console.log('✓ 数据库连接成功\n')
  } catch (error) {
    console.error('✗ 数据库连接失败:', error.message)
    console.error(error.stack)
    return
  }

  // 测试记忆管理器
  console.log('2. 测试记忆管理器...')
  try {
    const memoryManager = require('./src/memory/memory-manager')
    await memoryManager.init()
    console.log('✓ 记忆管理器初始化成功\n')

    // 测试创建用户档案
    const profile = await memoryManager.getUserProfile('test_user')
    console.log('✓ 用户档案:', profile)
  } catch (error) {
    console.error('✗ 记忆管理器失败:', error.message)
    console.error(error.stack)
    return
  }

  // 测试情感管理器
  console.log('\n3. 测试情感管理器...')
  try {
    const emotionManager = require('./src/memory/emotion-manager')
    await emotionManager.init()
    console.log('✓ 情感管理器初始化成功')

    const result = emotionManager.analyzeEmotion('我喜欢你', 50)
    console.log('✓ 情感分析:', result)
  } catch (error) {
    console.error('✗ 情感管理器失败:', error.message)
    console.error(error.stack)
    return
  }

  // 测试时间管理器
  console.log('\n4. 测试时间管理器...')
  try {
    const timeManager = require('./src/memory/time-manager')
    const timeInfo = timeManager.getCurrentTimeInfo()
    console.log('✓ 时间信息:', timeInfo)

    timeManager.recordInteraction('test_user')
    const context = timeManager.generateTimeContext('test_user')
    console.log('✓ 时间上下文:\n', context)
  } catch (error) {
    console.error('✗ 时间管理器失败:', error.message)
    console.error(error.stack)
    return
  }

  // 测试多层 AI
  console.log('\n5. 测试多层 AI...')
  try {
    const multiAI = require('./src/ai-multi-layer')
    console.log('✓ 多层 AI 加载成功')

    // 测试 Claude
    console.log('→ 测试 Claude...')
    const reply = await multiAI.chat(
      [{ role: 'user', content: '你好' }],
      '简短回复'
    )
    console.log('✓ Claude 回复:', reply)
  } catch (error) {
    console.error('✗ 多层 AI 失败:', error.message)
    console.error(error.stack)
  }

  // 测试权限管理器
  console.log('\n6. 测试权限管理器...')
  try {
    const { PermissionManager, PERMISSION_LEVELS } = require('./src/skills/permission-manager')
    const pm = new PermissionManager()
    pm.setUserPermission('test_user', PERMISSION_LEVELS.VIP)
    const level = pm.getUserPermission('test_user')
    console.log('✓ 权限等级:', pm.getPermissionName(level))

    const commands = pm.getAvailableCommands('test_user')
    console.log('✓ 可用命令数:', commands.length)
  } catch (error) {
    console.error('✗ 权限管理器失败:', error.message)
    console.error(error.stack)
  }

  console.log('\n✅ 所有测试完成')
}

testSystems().catch(console.error)
