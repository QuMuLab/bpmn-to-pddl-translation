(define (domain place_order_no_flatten)
  (:requirements :strips :typing)
  (:types task event gateway)

  (:predicates
    (StartEvent_1mnut37)
    (EndEvent_01a6rq8)
    (EndEvent_0nfuudw)
    (Task_0iirfhd)
    (Task_02fdytg)
    (Task_04aofbe)
    (Task_12lthpj)
    (Task_0eti3m2)
    (Task_1qlbv5i)
    (Task_1w7bb1w)
    (Task_1bwmf45)
    (Task_0yan60f)
    (IntermediateCatchEvent_1ias0p2)
    (IntermediateCatchEvent_037r6f2)
    (IntermediateCatchEvent_0d430z1)
    (EventBasedGateway_0qdxz70)
    (ExclusiveGateway_092mc05)
    (ExclusiveGateway_0lk2nir)
    (done)
    (started)
  )

  (:action start_probable_recourse_detected
    :precondition (and (not (started))(not (StartEvent_1mnut37)))
    :effect (and (StartEvent_1mnut37) (started))
  )

  (:action check_case
    :precondition (and (StartEvent_1mnut37))
    :effect (and (ExclusiveGateway_092mc05) (not (StartEvent_1mnut37)))
  )

  (:action send_request_for_payment
    :precondition (and (Task_02fdytg))
    :effect (and (Task_12lthpj) (not (Task_02fdytg)))
  )

  (:action close_case
    :precondition (and (Task_04aofbe))
    :effect (and (EndEvent_01a6rq8) (not (Task_04aofbe)))
  )

  (:action send_reminder
    :precondition (and (Task_12lthpj))
    :effect (and (EventBasedGateway_0qdxz70) (not (Task_12lthpj)))
  )

  (:action check_reasoning
    :precondition (and (IntermediateCatchEvent_1ias0p2))
    :effect (and (ExclusiveGateway_0lk2nir) (not (IntermediateCatchEvent_1ias0p2)))
  )

  (:action close_case_2
    :precondition (and (Task_1qlbv5i))
    :effect (and (EndEvent_01a6rq8) (not (Task_1qlbv5i)))
  )

  (:action hand_over_to_collection_agency_from_ExclusiveGateway_0lk2nir
    :precondition (and (Task_1w7bb1w))
    :effect (and (EndEvent_0nfuudw) (not (Task_1w7bb1w)))
  )

  (:action hand_over_to_collection_agency_from_IntermediateCatchEvent_037r6f2
    :precondition (and (IntermediateCatchEvent_037r6f2))
    :effect (and (EndEvent_0nfuudw) (not (IntermediateCatchEvent_037r6f2)))
  )

  (:action make_booking
    :precondition (and (IntermediateCatchEvent_0d430z1))
    :effect (and (Task_0yan60f) (not (IntermediateCatchEvent_0d430z1)))
  )

  (:action close_case_3
    :precondition (and (Task_0yan60f))
    :effect (and (EndEvent_01a6rq8) (not (Task_0yan60f)))
  )

  (:action event_EventBasedGateway_0qdxz70
    :precondition (and (EventBasedGateway_0qdxz70))
    :effect (and (oneof (IntermediateCatchEvent_1ias0p2) (IntermediateCatchEvent_037r6f2) (IntermediateCatchEvent_0d430z1)) (not (EventBasedGateway_0qdxz70)))
  )

  (:action exclusive_recourse_possible_
    :precondition (and (ExclusiveGateway_092mc05))
    :effect (and (oneof (Task_02fdytg) (Task_04aofbe)) (not (ExclusiveGateway_092mc05)))
  )

  (:action exclusive_OK_
    :precondition (and (ExclusiveGateway_0lk2nir))
    :effect (and (oneof (Task_1qlbv5i) (Task_1w7bb1w)) (not (ExclusiveGateway_0lk2nir)))
  )

  (:action goal_case_closed
    :precondition (and (EndEvent_01a6rq8))
    :effect (done)
  )

  (:action goal_case_open
    :precondition (and (EndEvent_0nfuudw))
    :effect (done)
  )

)