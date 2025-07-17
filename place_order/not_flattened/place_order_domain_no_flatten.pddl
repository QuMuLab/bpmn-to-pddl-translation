(define (domain place_order)
  (:requirements :strips :typing)
  (:types task event gateway)

  (:predicates
    (StartEvent_1)
    (Event_12xfkhi)
    (Activity_0fclwek)
    (Activity_08v385w)
    (Activity_0hpwxsm)
    (Activity_1wqi2kf)
    (Activity_1x6npxm)
    (Activity_1vopca8)
    (Gateway_1nuiirw)
    (Gateway_1yg27bh)
    (Gateway_1la9igl)
    (Gateway_04hl5tz)
    (Gateway_04hl5tz_precondition_0)
    (Gateway_04hl5tz_precondition_1)
    (done)
    (started)
  )

  (:action start_Order_Received
    :precondition (and (not (started))(not (StartEvent_1)))
    :effect (and (StartEvent_1) (started))
  )

  (:action Process_Order
    :precondition (and (StartEvent_1))
    :effect (and (Gateway_1nuiirw) (not (StartEvent_1)))
  )

  (:action produce_fresh_product
    :precondition (and (Activity_08v385w))
    :effect (and (Gateway_1yg27bh) (not (Activity_08v385w)))
  )

  (:action use_old_product_from_stock
    :precondition (and (Activity_0hpwxsm))
    :effect (and (Gateway_1yg27bh) (not (Activity_0hpwxsm)))
  )

  (:action Organize_Shipment
    :precondition (and (Activity_1wqi2kf))
    :effect (and (Gateway_04hl5tz) (Gateway_04hl5tz_precondition_0) (not (Activity_1wqi2kf)))
  )

  (:action Package_Goods
    :precondition (and (Activity_1x6npxm))
    :effect (and (Gateway_04hl5tz) (Gateway_04hl5tz_precondition_1) (not (Activity_1x6npxm)))
  )

  (:action Ship_Order
    :precondition (and (Activity_1vopca8))
    :effect (and (Event_12xfkhi) (not (Activity_1vopca8)))
  )

  (:action exclusive_Order_value_above_25_000___
    :precondition (and (Gateway_1nuiirw))
    :effect (and (oneof (Activity_08v385w) (Activity_0hpwxsm)) (not (Gateway_1nuiirw)))
  )

  (:action exclusive_Gateway_1yg27bh
    :precondition (and (Gateway_1yg27bh))
    :effect (and (Gateway_1la9igl) (not (Gateway_1yg27bh)))
  )

  (:action parallel_Gateway_1la9igl
    :precondition (and (Gateway_1la9igl))
    :effect (and (Activity_1wqi2kf) (Activity_1x6npxm) (not (Gateway_1la9igl)))
  )

  (:action parallel_Gateway_04hl5tz
    :precondition (and (Gateway_04hl5tz) (Gateway_04hl5tz_precondition_0) (Gateway_04hl5tz_precondition_1))
    :effect (and (Activity_1vopca8) (not (Gateway_04hl5tz)))
  )

  (:action goal_Order_Processed
    :precondition (and (Event_12xfkhi))
    :effect (done)
  )

)