from place_order import *

def process_side(client, 
                 token, 
                 current_buy_orders, 
                 current_sell_orders, 
                 market_ids, 
                 token_ids,
                 token_id_side, 
                 size, 
                 question, 
                 buy_order_times,
                 best_bid,
                 ):
    
    """
    处理单边的订单逻辑：
      1. 检查买单状态；
      2. 当买单成交且该边尚未有卖单时，下对应边的卖单；
      3. 检查卖单状态，如已成交则下新的买单。
    """

    market_id = market_ids.get(token)
    if not market_id:
        logger.error(f"[{question}] 未知的 {token.upper()} 市场信息，无法处理订单。")
    
    ##############################################################################################################################################################################
    
    ###############################
    # 1. 检查买单状态
    ###############################
    if current_buy_orders.get(token):
        
        buy_order_id = current_buy_orders[token][0].get("id") # 特定问题的 买单的 特定token的 特定id
        best_bid_price = max(float(order.price) for order in client.get_order_book(token_id_side[token]).bids)  # 获取当前的best_bid

        ######################################################################################
        # 1.1 检查买单状态，如果 超时 并且 best bid 发生变化那么就cancel重新下单，如果没超时 或 best bid 无变化 就查看买单是否全部成交 （2）
        ######################################################################################
        if int(time.time()) - buy_order_times[token].get(buy_order_id) > 60 and float(best_bid_price) != float(best_bid[token]):  # 超过一定时间 并且 最优买单价格发生了变化
            
            logger.warning(f"[{question}] {token.upper()} 买单超时，且最优买单价格发生了变化。")
            
            # 再取消订单之前要把没完全买进来的shares卖掉            
            # 如果 恰好买单全进去了，那么有可能会导致这个buy_matched_size找不到，因为get_orders里面没有这个买单id了
            buy_matched_size = next((order.get('size_matched') 
                                    for order in client.get_orders(OpenOrderParams(market=market_id)) 
                                    if order.get('id') == buy_order_id), None)

            # buy_matched_size is not None 说明这个买单还存在

            ########
            # 1.1.1
            ########
            
            if buy_matched_size is not None and float(buy_matched_size) == float(0):
                logger.warning(f'[{question}] {token.upper()} 的上一买单 没有任何成交，直接cancel')
                
                client.cancel(order_id=buy_order_id) # 取消订单   
                #####清空######
                current_buy_orders[token] = [] # 1 清空 buy order
                buy_order_id = '' # 2 清空 buy_order_id
                best_bid[token] = [] # 3 清空 best bid
                del buy_order_times[token][buy_order_id] # 4 删除旧的买单时间记录
                    
                ##############################################################################################
                # 重新下新的买单
                buy_orders_resp = place_buy_orders(client, 
                                                    token_ids, 
                                                    market_id, 
                                                    size, 
                                                    question, 
                                                    token)
                
                print('11111111111111111111111111111上一买单已取消，下新买单111111111111111111111111111111')
                        
                if buy_orders_resp.get(token):
                    logger.info(f"[{question}] {token.upper()} 新买单已下单")
                            
                    #####更新######
                    current_buy_orders[token] = buy_orders_resp[token] # 1 更新 current_buy_orders
                    buy_order_id = current_buy_orders[token][0].get("id") # 2 更新 buy_order_id
                    buy_order_times[token][buy_order_id] = current_buy_orders[token][0].get('created_at')  # 3 更新 buy_order_times
                    best_bid[token] = current_buy_orders[token][0].get("price") # 4 更新 best bid价格

                else:
                    logger.error(f"[{question}] {token.upper()} 新买单下单失败。")
                ##############################################################################################      
            
            ########
            # 1.1.2
            ########

            elif buy_matched_size is not None and float(0) < float(buy_matched_size) < float(5): # 挂limit sell order 至少要有 5个share
                logger.warning(f'[{question}] 的上一买单 {token.upper()} 成交量大于0但是不足5个share，等待直到大于等于5个share成立')
            # ERROR - [Will GPT-5 be released by June 30?]; YES, sell, Order placement failed: PolyApiException[status_code=400, error_message={'error': 'order 0x85eef06f73d9567d57a21bc310ce653e08691dabfacfd5e6412e55c3b296a01b is invalid. Size (4.9) lower than the minimum: 5'}]

            ########
            # 1.1.3
            ########
            elif buy_matched_size is not None and float(5) <= float(buy_matched_size) < float(size):
                 
                logger.warning(f'[{question}] 的上一买单 {token.upper()} 大于等于5个share成交，有{float(buy_matched_size)}成交')
                sell_partial = place_sell_orders(client, 
                                                token_ids, 
                                                market_id, 
                                                int(float(buy_matched_size) * 100) / 100, 
                                                question, 
                                                token)
                print('11111111111111111111111111111卖掉上一order不足size的order111111111111111111111111111111')
                # 因为这里面卖的数量不是一开始定义的完整的size，所以不记录
                
                if sell_partial and sell_partial.get(token):
                    logger.info(f"[{question}] 的上一买单 {token.upper()} 进position的部分已卖出，现在可以cancel上一买单")   
                
            
                client.cancel(order_id=buy_order_id) # 取消订单   
                #####清空######
                current_buy_orders[token] = [] # 1 清空 buy order
                buy_order_id = '' # 2 清空 buy_order_id
                best_bid[token] = [] # 3 清空 best bid
                del buy_order_times[token][buy_order_id] # 4 删除旧的买单时间记录
                    
                ##############################################################################################
                # 重新下新的买单
                buy_orders_resp = place_buy_orders(client, 
                                                    token_ids, 
                                                    market_id, 
                                                    size, 
                                                    question, 
                                                    token)
                print('11111111111111111111111111111上一买单已取消，下新买单111111111111111111111111111111')
                        
                if buy_orders_resp.get(token):
                    logger.info(f"[{question}] {token.upper()} 新买单已下单")
                            
                    #####更新######
                    current_buy_orders[token] = buy_orders_resp[token] # 1 更新 current_buy_orders
                    buy_order_id = current_buy_orders[token][0].get("id") # 2 更新 buy_order_id
                    buy_order_times[token][buy_order_id] = current_buy_orders[token][0].get('created_at')  # 3 更新 buy_order_times
                    best_bid[token] = current_buy_orders[token][0].get("price") # 4 更新 best bid价格

                else:
                    logger.warning(f"[{question}] {token.upper()} 新买单下单失败。")
                ##############################################################################################

        else:
            logger.warning(f"[{question}] {token.upper()} 买单没有超时 或 最优买单价格没有发生变化。") 

    else:
        logger.warning(f"[{question}] {token.upper()} 无买单挂单。")    
    
    ######################################################################################################################################################################
    time.sleep(1)   

    ##################################
    # 2. 检查买单是否全部成交
    ##################################
    
    if not any(order.get("id") == buy_order_id for order in client.get_orders(OpenOrderParams(market=market_id))): # 若在更新的订单中找不到该买单，认为订单已全部成交
            logger.info(f"[{question}] {token.upper()} 买单已全部成交。")
                            
            #####清空######
            current_buy_orders[token] = [] # 1 清空 buy order
            buy_order_id = '' #2 清空 buy_order_id
            best_bid[token] = [] # 3 清空 best bid
            del buy_order_times[token][buy_order_id]  # 4 删除成交的买单时间记录
            
            time.sleep(3)         

            ########################
            # 买单全部成交后，全部下卖单
            ########################
            if not current_buy_orders.get(token) and not current_sell_orders.get(token): # 如果买单没有记录 且 卖单还没有记录
                logger.info(f"[{question}] {token.upper()} 开始下卖单。")

                sell_orders = place_sell_orders(client, 
                                                token_ids, 
                                                market_id, 
                                                size - 0.01, # 买单全部成交时下的卖单
                                                question, 
                                                token)
                
                print('11111111111111111111111111111买单全部成交，下卖单111111111111111111111111111111')
                    
                if sell_orders and sell_orders.get(token):
                        
                    #####更新######
                    current_sell_orders[token] = sell_orders[token] # 1 更新sell orders
                    sell_order_id = current_sell_orders[token][0].get("id") # 2 更新 sell_order_id

                    logger.info(f"[{question}] {token.upper()} 卖单已下单，订单ID: {sell_order_id}")
                else:
                    logger.error(f"[{question}] {token.upper()} 卖单下单失败。")
                                                
    else:
        logger.warning(f"[{question}] {token.upper()} 买单没有全部成交，仍在挂单中。")
    
    
    
    ################
    # 4. 检查卖单状态
    ################
    if current_sell_orders.get(token):        
        
        #####################
        # 4.1 如果所有卖单都成交
        #####################
        if not any(order.get("id") == current_sell_orders[token][0].get("id") for order in client.get_orders(OpenOrderParams(market=market_id))):
            logger.info(f"[{question}] {token.upper()} 卖单已全部成交。")
                
            current_sell_orders[token] = []
                
            ##############################################################################################
            # 重新下新的买单
            buy_orders_resp = place_buy_orders(client, 
                                                token_ids, 
                                                market_id, 
                                                size, 
                                                question, 
                                                token)
                        
            if buy_orders_resp and buy_orders_resp.get(token):
                    
                #####更新######
                current_buy_orders[token] = buy_orders_resp[token] # 1 更新 current_buy_orders
                buy_order_id = current_buy_orders[token][0].get("id")
                buy_order_times[token][buy_order_id] = current_buy_orders[token][0].get('created_at')  # 2 更新 buy_order_times
                best_bid[token] = current_buy_orders[token][0].get("price") # 3 更新 best bid价格

                logger.info(f"[{question}] {token.upper()} 新买单已下单")
            else:
                logger.error(f"[{question}] {token.upper()} 新买单下单失败。")
            ##############################################################################################
                    
        else:
            logger.warning(f"[{question}] {token.upper()} 卖单仍在挂单中。")
    else:
        logger.warning(f"[{question}] {token.upper()} 当前无卖单挂单。")
    ##############################################################################################################################################################
    time.sleep(1)



# # buy_orders: {
# #           'no': [{'id': '0x0e3e4d66129d7c1a44ca3e8beb22b7ff5188fdd33351aa7e7c81ec0471046f8e', 
# #                      'status': 'LIVE', 
# #                      'owner': 'cde75286-a1c7-a5b7-b00f-f21ac99f6fba', 
# #                      'maker_address': '0xCA3095B81B1Af8b0096150f065e9c4330d4B8042', 
# #                      'market': '0xaf1a2b4ccf8b92efc3710b5d3bb263aa28c9ecf4858abb6c73047c1c0d7b9416', 
# #                       'asset_id': '52170441229254093239180420557188676391777309638074470699644705957928403317548', 
# #                       'side': 'BUY', 'original_size': '20', 'size_matched': '0', 
# #                       'price': '0.861', 'outcome': 'No', 'expiration': '0', 
# #                       'order_type': 'GTC', 'associate_trades': [], 'created_at': 1739822859}], 

# #             'yes': [{'id': '0xbff46f0f8211d4f4048126a101e8108fbb80fd594e48412c6cfde619389ce745', 
# #                      'status': 'LIVE', 
# #                       'owner': 'cde75286-a1c7-a5b7-b00f-f21ac99f6fba', 
# #                      'maker_address': '0xCA3095B81B1Af8b0096150f065e9c4330d4B8042', 
# #                      'market': '0xaf1a2b4ccf8b92efc3710b5d3bb263aa28c9ecf4858abb6c73047c1c0d7b9416', 
# #                      'asset_id': '50590995350569541543130773217099833464734527698164475480567020627331537312844', 
# #                       'side': 'BUY', 'original_size': '20', 'size_matched': '0', 
# #                       'price': '0.134', 'outcome': 'Yes', 'expiration': '0', 'order_type': 'GTC', 
# #                       'associate_trades': [], 'created_at': 1739822859}]
# #                       }


########################
########################
########################

def execute_trade(client, question, trade_info, size):
    """
    处理单个交易对的下单与持续交易流程。

    :param client: 交易客户端对象
    :param question: 交易问题/标识
    :param trade_info: 包含 'TokenID'、'conditionId'、'spread' 的字典
    :param size: 每笔订单的数量
    """
    token_ids = trade_info.get("TokenID")
    conditionId = trade_info.get("conditionId")
    spread = trade_info.get("spread")

    ########################
    ####对于每个question#####
    ########################

    
    # 将问题、条件ID 与 spread 信息组合到日志标识中
    header = f"{question} (market condition: {conditionId}, spread: {spread})"
    logger.info(f"开始交易: {header}")
    
    # 2
#   保存每个yes或者no的 token_id 信息，防止后续订单列表清空后无法获取 token_id
    market_ids = {'yes': conditionId, 'no': conditionId}
    token_id_side = {'yes': token_ids[0], 'no': token_ids[1]} 
    
     # 3
#   为每个 question 创建独立的 initial_buy_orders
    initial_buy_orders = {
        "yes": place_buy_orders(client, token_ids, conditionId, size, question=question, side="yes").get("yes"),
        "no": place_buy_orders(client, token_ids, conditionId, size, question=question, side="no").get("no")
    }
    
    if not all(initial_buy_orders.values()):
        logger.error(f"{question} 初始买单下单失败，终止该交易。")
        return

    logger.info(f"{question} 初始买单下单成功: {initial_buy_orders}")

    # 4
#   为每个 question 创建独立的 buy_order_times
    buy_order_times = {
        side: {orders[0].get("id"): orders[0].get("created_at")}
        for side, orders in initial_buy_orders.items() if orders
    }
    
    # 5
#    为每个 question 创建独立的 best_bid
#    记录下单时最佳买价
    best_bid = {
        'yes': initial_buy_orders['yes'][0].get("price"),
        'no': initial_buy_orders['no'][0].get("price")
    }
    
    # 7
#   为每个 question 创建独立的 current_sell_orders
#   记录卖单下单时的order
    current_sell_orders = {'yes': [], 'no': []}


#   ########################
#   ###在一个question里面#####
#   ####对于每个yes 和 no#####
#   ########################
        
#   current_buy_orders初始化最开始的买单
    current_buy_orders = initial_buy_orders

    # 启动持续交易循环（该函数内部应包含一个不断轮询、监控并处理订单的循环）
    # 进入持续交易循环：并发分别处理 'yes' 与 'no' 两边的订单逻辑
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        while True:
            futures = {
                executor.submit(
                    process_side,
                    client,
                    token,  # 'yes' 或 'no'
                    current_buy_orders,
                    current_sell_orders,
                    market_ids,
                    token_ids,
                    token_id_side,
                    size,
                    question,
                    buy_order_times,
                    best_bid,
                ): token for token in ['yes', 'no']
            }
            concurrent.futures.wait(futures)

def trade_pair(client, trade_dict, size):
    """
    同时处理多个 token 交易对（并行下单），交易字典格式为：
        key: 问题，
        value: 包含 'TokenID'、'conditionId'、'spread' 的字典
    每笔交易时将 conditionId 与 spread 信息也包含在日志中，方便确认每笔订单对应的条件。
    该函数将一直运行，持续进行买卖滚动交易。

    :param client: 交易客户端对象
    :param trade_dict: 交易字典，例如：
           {
               "问题1": {"TokenID": [yes_token_id, no_token_id], "conditionId": market_id1, "spread": spread1},
               "问题2": {"TokenID": [yes_token_id, no_token_id], "conditionId": market_id2, "spread": spread2},
               ...
           }
    :param size: 每笔订单的数量
    :return: 该函数不会退出，除非出现异常或被外部终止
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(trade_dict)) as executor:
        futures = []
        for question, trade_info in trade_dict.items():
            futures.append(executor.submit(execute_trade, client, question, trade_info, size))
        # 持续等待所有交易线程（由于持续交易循环，该等待理论上不会退出）
        concurrent.futures.wait(futures)

        
        
# initial_buy_orders: {
#           'no': [{'id': '0x0e3e4d66129d7c1a44ca3e8beb22b7ff5188fdd33351aa7e7c81ec0471046f8e', 
#                      'status': 'LIVE', 
#                      'owner': 'cde75286-a1c7-a5b7-b00f-f21ac99f6fba', 
#                      'maker_address': '0xCA3095B81B1Af8b0096150f065e9c4330d4B8042', 
#                      'market': '0xaf1a2b4ccf8b92efc3710b5d3bb263aa28c9ecf4858abb6c73047c1c0d7b9416', 
#                       'asset_id': '52170441229254093239180420557188676391777309638074470699644705957928403317548', 
#                       'side': 'BUY', 'original_size': '20', 'size_matched': '0', 
#                       'price': '0.861', 'outcome': 'No', 'expiration': '0', 
#                       'order_type': 'GTC', 'associate_trades': [], 'created_at': 1739822859}], 

#             'yes': [{'id': '0xbff46f0f8211d4f4048126a101e8108fbb80fd594e48412c6cfde619389ce745', 
#                      'status': 'LIVE', 
#                       'owner': 'cde75286-a1c7-a5b7-b00f-f21ac99f6fba', 
#                      'maker_address': '0xCA3095B81B1Af8b0096150f065e9c4330d4B8042', 
#                      'market': '0xaf1a2b4ccf8b92efc3710b5d3bb263aa28c9ecf4858abb6c73047c1c0d7b9416', 
#                      'asset_id': '50590995350569541543130773217099833464734527698164475480567020627331537312844', 
#                       'side': 'BUY', 'original_size': '20', 'size_matched': '0', 
#                       'price': '0.134', 'outcome': 'Yes', 'expiration': '0', 'order_type': 'GTC', 
#                       'associate_trades': [], 'created_at': 1739822859}]
#                       }
        


## 没完全成交的订单状态
# [{'id': '0x56d2d840a9401ec9c4851426aac8ae6d86b12763a5c3600c2c5e11df037007ca',
#   'status': 'LIVE',
#   'owner': 'da9dceae-36b9-5b25-efed-a720b85a68dc',
#   'maker_address': '0x7aC4Fb15368d2b62C8ebb6B9B50F8b568f0dd649',
#   'market': '0x2090c30d181142250d1f25b5da4808b16cddd7f2e2cfcf19bdfd508325498fb6',
#   'asset_id': '89768568686584036399418990202600408525021143064935199774078963108133813129029',
#   'side': 'SELL',
#   'original_size': '40',
#   'size_matched': '10',
#   'price': '0.61',
#   'outcome': 'Yes',
#   'expiration': '0',
#   'order_type': 'GTC',
#   'associate_trades': ['127414fc-cdcd-4116-9829-33130f308c81'],
#   'created_at': 1740017091}]


 
  # 示例：定义包含问题和对应 token_id 列表的字典
trade_tokens_dict = {
        
'Fed decreases interest rates by 25 bps after June 2025 meeting?': {'TokenID': ['72590024726245493077522454398168089576836207607927418208000602748203871211427',
   '36390717936372746391289704283263123445079118730599731659392294228980748319183'],
  'conditionId': '0x872c8e9a4e4808a2ab714c267bd8a93f63cb739c853d7e4de2b42009e73f9b3f',
  'spread': 0.03}
#  'DOGE prosecutes US Treasury?': {'TokenID': ['59629731301419869629910017653328580920572662251843909206058959836751828680335',
#    '5522892390429754827964706964735514912217688543655936791393227579472781730068'],
#   'conditionId': '0x63aaa2943c7b2ccff81ed89916ce1636787051b00330433e70f50f8f619568bb',
#   'spread': 0.03},
#  'Will Bitcoin reach $110,000 by December 31, 2025?': {'TokenID': ['39044137795224187219385013942783323059681835335864307732029139183983670488070',
#    '13660516767041361627171788514669314634677119276162516861586896150850746376938'],
#   'conditionId': '0x63e3c9432d9e3a0e9665d1152fc0a05f6ed17c9033eb9290062d25d2afb2bed5',
#   'spread': 0.039}
}

# 运行交易
trade_pair(client, trade_tokens_dict, size = float(10))