(define (domain self_serve_restaurant)
  (:requirements :strips :typing)
  (:types task event gateway)

  (:predicates
    (StartEvent_1jrp9jr)
    (StartEvent_02hitoh)
    (StartEvent_0zymmrx)
    (EndEvent_0t0z07x)
    (EndEvent_1mxdcfl)
    (EndEvent_1pmnzaw)
    (Task_1kt8dzo)
    (Task_1udyby3)
    (Task_0a2rm9v)
    (Task_12h2fs9)
    (Task_1jlgbwe)
    (Task_0o0pue9)
    (Task_07amhtq)
    (Task_1y7mm27)
    (Task_1ng51gy)
    (Task_03wsmkw)
    (Task_0ttgn0d)
    (Task_1wgretj)
    (Task_12zp7cy)
    (Task_1a48xz1)
    (Task_0rpvccw)
    (Task_0av6xl6)
    (Task_1tdsk5o)
    (Task_0ot5dif)
    (IntermediateCatchEvent_1nu2fvu)
    (IntermediateCatchEvent_1r5wlb4)
    (IntermediateCatchEvent_1pl0nlh)
    (IntermediateCatchEvent_1rch6yh)
    (IntermediateCatchEvent_0nhl104)
    (EventBasedGateway_1qyi8l9)
    (done)
    (started)
  )

  (:action start_process
    :precondition (and (not (started)) (not (StartEvent_1jrp9jr)) (not (StartEvent_02hitoh)) (not (StartEvent_0zymmrx)))
    :effect (and (oneof (StartEvent_1jrp9jr) (StartEvent_02hitoh) (StartEvent_0zymmrx)) (started))
  )

  (:action Enter_restaurant
    :precondition (and (StartEvent_1jrp9jr))
    :effect (and (Task_1udyby3) (not (StartEvent_1jrp9jr)))
  )

  (:action Choose_dish
    :precondition (and (Task_1udyby3))
    :effect (and (IntermediateCatchEvent_1nu2fvu) (not (Task_1udyby3)))
  )

  (:action Place_order
    :precondition (and (IntermediateCatchEvent_1nu2fvu))
    :effect (and (Task_12h2fs9) (not (IntermediateCatchEvent_1nu2fvu)))
  )

  (:action Pay_money
    :precondition (and (Task_12h2fs9))
    :effect (and (Task_1jlgbwe) (not (Task_12h2fs9)))
  )

  (:action Take_buzzer
    :precondition (and (Task_1jlgbwe))
    :effect (and (IntermediateCatchEvent_1r5wlb4) (not (Task_1jlgbwe)))
  )

  (:action Get_meal
    :precondition (and (IntermediateCatchEvent_1r5wlb4))
    :effect (and (Task_07amhtq) (not (IntermediateCatchEvent_1r5wlb4)))
  )

  (:action Eat_meal
    :precondition (and (Task_07amhtq))
    :effect (and (EndEvent_0t0z07x) (not (Task_07amhtq)))
  )

  (:action Enter_order
    :precondition (and (StartEvent_02hitoh))
    :effect (and (Task_1ng51gy) (not (StartEvent_02hitoh)))
  )

  (:action Collect_money
    :precondition (and (Task_1ng51gy))
    :effect (and (Task_03wsmkw) (not (Task_1ng51gy)))
  )

  (:action Set_up_buzzer
    :precondition (and (Task_03wsmkw))
    :effect (and (Task_0ttgn0d) (not (Task_03wsmkw)))
  )

  (:action Hand_over_buzzer
    :precondition (and (Task_0ttgn0d))
    :effect (and (Task_1wgretj) (not (Task_0ttgn0d)))
  )

  (:action Inform_chef
    :precondition (and (Task_1wgretj))
    :effect (and (IntermediateCatchEvent_1pl0nlh) (not (Task_1wgretj)))
  )

  (:action Set_off_buzzer
    :precondition (and (IntermediateCatchEvent_1pl0nlh))
    :effect (and (EventBasedGateway_1qyi8l9) (not (IntermediateCatchEvent_1pl0nlh)))
  )

  (:action Hand_over_meal
    :precondition (and (IntermediateCatchEvent_1rch6yh))
    :effect (and (EndEvent_1mxdcfl) (not (IntermediateCatchEvent_1rch6yh)))
  )

  (:action Call_guest
    :precondition (and (IntermediateCatchEvent_0nhl104))
    :effect (and (EventBasedGateway_1qyi8l9) (not (IntermediateCatchEvent_0nhl104)))
  )

  (:action Prepare_meal
    :precondition (and (StartEvent_0zymmrx))
    :effect (and (Task_1tdsk5o) (not (StartEvent_0zymmrx)))
  )

  (:action Place_meal_in_hatch
    :precondition (and (Task_1tdsk5o))
    :effect (and (Task_0ot5dif) (not (Task_1tdsk5o)))
  )

  (:action Inform_employee
    :precondition (and (Task_0ot5dif))
    :effect (and (EndEvent_1pmnzaw) (not (Task_0ot5dif)))
  )

  (:action event_EventBasedGateway_1qyi8l9
    :precondition (and (EventBasedGateway_1qyi8l9))
    :effect (and (oneof (IntermediateCatchEvent_1rch6yh) (IntermediateCatchEvent_0nhl104)) (not (EventBasedGateway_1qyi8l9)))
  )

  (:action goal_Not_hungry_anymore
    :precondition (and (EndEvent_0t0z07x))
    :effect (done)
  )

  (:action goal_Order_processed
    :precondition (and (EndEvent_1mxdcfl))
    :effect (done)
  )

  (:action goal_Meal_prepared
    :precondition (and (EndEvent_1pmnzaw))
    :effect (done)
  )

)