from initial import *


def place_limit_order(client, token_id, market_id, price, size, order_side, action, question=None):
    """
    发送限价订单（买单或卖单）到 Polymarket CLOB 交易所，并在日志中带上 question 标识
    :param client: CLOB 交易客户端
    :param token_ids: 包含 Yes 和 No 的 Token ID 列表
    :param price: 订单价格
    :param size: 订单数量
    :param order_side: "yes" 或 "no"
    :param action: "buy" 或 "sell"
    :param question: 该交易对应的问题（字符串），用于日志标识
    :return: 订单响应
    """

    if action.lower() == "buy":
        side = BUY
    elif action.lower() == "sell":
        side = SELL
    else:
        logger.error("Invalid action. Choose 'buy' or 'sell'.")
        return None

    header = f"[{question}]" if question else ""
    
    try:
        logger.info(f"{header} Placing limit {action.upper()} order for {order_side.upper()} with price {price} and size {size}...")
        logger.info("-" * 20)
        
        create_and_post_order = client.create_and_post_order(
            OrderArgs(
                price=price,
                size=size,
                side=side,
                token_id=token_id
            )
        )
        

        order_resp = client.get_orders(
            OpenOrderParams(
                market=market_id,
            )
        )

        # print(order_resp)
        
        
        logger.info(f"{header} {order_side.upper()} If order success response: {create_and_post_order.get('success')}")
        logger.info("-" * 20)
        
        # return order_resp
        return order_resp, create_and_post_order

    except Exception as e:
        logger.error(f"{header}; {order_side.upper()}, {action}, Order placement failed: {e}")
        logger.info("-" * 20)
        return None
    

# RES, _ =  place_limit_order(client, 
#                   '71997651913152206570629088321956120864079718576170044443758559799563717452631',
#                 #   '18341035027714870637048620309684171909563203591233792130567981491497950451598'], 
#                   '0x38f1ef47821249f229245352d5deee604d95fb0c86aa4cd0e4892223d0d1aa37', 
#                   0.26, 
#                   20, 
#                   'YES', 
#                   BUY, 
#                   question=None)

# RES


# [{'id': '0x70c4722df13fbe007a1f02e1c4da9ec5a576a31f6c194048eb6c1c9a3f990075',
#   'status': 'LIVE',
#   'owner': 'cde75286-a1c7-a5b7-b00f-f21ac99f6fba',
#   'maker_address': '0xCA3095B81B1Af8b0096150f065e9c4330d4B8042',
#   'market': '0x38f1ef47821249f229245352d5deee604d95fb0c86aa4cd0e4892223d0d1aa37',
#   'asset_id': '71997651913152206570629088321956120864079718576170044443758559799563717452631',
#   'side': 'BUY',
#   'original_size': '20',
#   'size_matched': '0',
#   'price': '0.26',
#   'outcome': 'Yes',
#   'expiration': '0',
#   'order_type': 'GTC',
#   'associate_trades': [],
#   'created_at': 1739846768}]

    

# RES, _ =  place_limit_order(client, 
#                   '71997651913152206570629088321956120864079718576170044443758559799563717452631',
#                 #   '18341035027714870637048620309684171909563203591233792130567981491497950451598'], 
#                   '0x38f1ef47821249f229245352d5deee604d95fb0c86aa4cd0e4892223d0d1aa37', 
#                   0.26, 
#                   20, 
#                   'YES', 
#                   BUY, 
#                   question=None)

# RES


# [{'id': '0x70c4722df13fbe007a1f02e1c4da9ec5a576a31f6c194048eb6c1c9a3f990075',
#   'status': 'LIVE',
#   'owner': 'cde75286-a1c7-a5b7-b00f-f21ac99f6fba',
#   'maker_address': '0xCA3095B81B1Af8b0096150f065e9c4330d4B8042',
#   'market': '0x38f1ef47821249f229245352d5deee604d95fb0c86aa4cd0e4892223d0d1aa37',
#   'asset_id': '71997651913152206570629088321956120864079718576170044443758559799563717452631',
#   'side': 'BUY',
#   'original_size': '20',
#   'size_matched': '0',
#   'price': '0.26',
#   'outcome': 'Yes',
#   'expiration': '0',
#   'order_type': 'GTC',
#   'associate_trades': [],
#   'created_at': 1739846768}]



########################
########################
######下best bid买单#####
########################
########################



def place_buy_orders(client, token_ids, market_id, size, question, side):
    """
    下买单。仅下指定边（"yes" 或 "no"）的买单。
    :param client: 交易客户端对象
    :param token_ids: 包含 Yes 和 No 的 Token ID 列表，顺序须与逻辑一致（[yes_token, no_token]）
    :param market_id: 市场 ID
    :param size: 订单数量
    :param question: 该交易对应的问题（字符串）
    :param side: 必须传入 "yes" 或 "no"，表示下对应边的买单。
    :return: 下单成功的 buy_orders 字典；如果未成功，则返回 None
    """
    cur_side = side.lower()
    if cur_side not in ["yes", "no"]:
        logger.error(f"[{question}] side 参数无效：{side}。必须为 'yes' 或 'no'。")
        return None

    token_id = token_ids[0] if cur_side == 'yes' else token_ids[1]
    order_book = client.get_order_book(token_id)
    if not order_book:
        logger.error(f"[{question}] 无法获取 {cur_side.upper()} 订单簿数据，跳过 {cur_side.upper()} 买单。")
        logger.info("-" * 20)
        return None

    try:
        # 计算最佳买单价格，假设 order_book.bids 是对象列表且 order.price 可转换为 float
        best_bid = max(float(order.price) for order in order_book.bids)
        # logger.info(f"[{question}] {cur_side.upper()} optimal bid is: {best_bid}")
        # logger.info("-" * 20)
    except Exception as e:
        logger.error(f"[{question}] 计算 {cur_side.upper()} 最佳 bid 价格时出错: {e}")
        logger.info("-" * 20)
        return None

    # 下买单
    buy_resp, _ = place_limit_order(
        client,
        token_id,
        market_id=market_id,
        price=best_bid,
        size=size,
        order_side=cur_side,
        action="buy",
        question=question
    )

    if buy_resp is None:
        logger.error(f"[{question}] {cur_side.upper()} 买单下单失败。")
        logger.info("-" * 20)
        return None

    # 过滤返回订单，仅保留 outcome 与当前 side 对应的订单
    expected_outcome = "Yes" if cur_side == "yes" else "No"
    filtered_orders = [order for order in buy_resp if order.get("outcome") == expected_outcome]

    if not filtered_orders:
        logger.error(f"[{question}] {cur_side.upper()} 买单返回的订单中没有符合条件的订单。")
        logger.info("-" * 20)
        return None

    buy_orders = {cur_side: filtered_orders}
    logger.info(f"[{question}] Buy Orders: {buy_orders}")
    return buy_orders


def place_sell_orders(client, token_ids, market_id, size, question, side):
    """
    下卖单。仅下指定边（"yes" 或 "no"）的卖单。
    :param client: 交易客户端对象
    :param token_ids: 包含 Yes 和 No 的 Token ID 列表，顺序须与逻辑一致（[yes_token, no_token]）
    :param market_id: 市场 ID
    :param size: 订单数量
    :param question: 该交易对应的问题（字符串）
    :param side: 必须传入 "yes" 或 "no"，表示下对应边的卖单。
    :return: 下单成功的 sell_orders 字典；如果未成功，则返回 None
    """
    cur_side = side.lower()
    if cur_side not in ["yes", "no"]:
        logger.error(f"[{question}] side 参数无效：{side}。必须为 'yes' 或 'no'。")
        return None

    token_id = token_ids[0] if cur_side == 'yes' else token_ids[1]
    order_book = client.get_order_book(token_id)
    if not order_book:
        logger.error(f"[{question}] 无法获取 {cur_side.upper()} 订单簿数据，跳过 {cur_side.upper()} 卖单。")
        logger.info("-" * 20)
        return None

    try:
        # 计算最佳卖单价格，假设 order_book.asks 是对象列表且 order.price 可转换为 float
        best_ask = min(float(order.price) for order in order_book.asks)
        # logger.info(f"[{question}] {cur_side.upper()} optimal ask is: {best_ask}")
        # logger.info("-" * 20)
    except Exception as e:
        logger.error(f"[{question}] 计算 {cur_side.upper()} 最佳 ask 价格时出错: {e}")
        logger.info("-" * 20)
        return None

    # 下卖单
    sell_resp, _ = place_limit_order(
        client,
        token_id,
        market_id=market_id,
        price=best_ask,
        size=size,
        order_side=cur_side,
        action="sell",
        question=question
    )

    if sell_resp is None:
        logger.error(f"[{question}] {cur_side.upper()} 卖单下单失败。")
        logger.info("-" * 20)
        return None

    # 过滤返回订单，仅保留 outcome 与当前 side 对应的订单
    expected_outcome = "Yes" if cur_side == "yes" else "No"
    filtered_orders = [order for order in sell_resp if order.get("outcome") == expected_outcome]

    if not filtered_orders:
        logger.error(f"[{question}] {cur_side.upper()} 卖单返回的订单中没有符合条件的订单。")
        logger.info("-" * 20)
        return None

    sell_orders = {cur_side: filtered_orders}
    logger.info(f"[{question}] Sell Orders: {sell_orders}")
    return sell_orders