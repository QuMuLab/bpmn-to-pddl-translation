(define (domain place_order_no_flatten)
  (:requirements :strips :typing)
  (:types task event gateway)

  (:predicates
    (StartEvent_1)
    (EndEvent_1fx9yp3)
    (Task_12j0pib)
    (Task_0jsoxba)
    (Task_0vaxgaa)
    (Task_0e6hvnj)
    (Task_0s79ile)
    (Task_05ftug5)
    (Task_0sl26uo)
    (ExclusiveGateway_1mpgzhg)
    (InclusiveGateway_0p2e5vq)
    (ExclusiveGateway_1ouv9kf)
    (ExclusiveGateway_0z5sib0)
    (ParallelGateway_02fgrfq)
    (InclusiveGateway_1dgb4sg)
    (inclusive_counter_InclusiveGateway_0p2e5vq_0)
    (inclusive_counter_InclusiveGateway_0p2e5vq_1)
    (inclusive_counter_InclusiveGateway_0p2e5vq_2)
    (increase_InclusiveGateway_0p2e5vq)
    (decrease_InclusiveGateway_0p2e5vq)
    (at_least_one_branch_InclusiveGateway_0p2e5vq)
    (branch_started_InclusiveGateway_0p2e5vq_Task_12j0pib)
    (branch_started_InclusiveGateway_0p2e5vq_Task_0jsoxba)
    (done)
    (started)
    (test1)
    (test2)
  )

  (:action start_Ship_goods
    :precondition (and (not (started))(not (StartEvent_1)))
    :effect (and (StartEvent_1) (started))
  )

  (:action activate_ParallelGateway_02fgrfq
    :precondition (and (StartEvent_1))
    :effect (and (ParallelGateway_02fgrfq) (not(StartEvent_1)))
  )

  (:action inclusive_increase_InclusiveGateway_0p2e5vq
    :precondition (and (increase_InclusiveGateway_0p2e5vq))
    :effect (and
      (not (increase_InclusiveGateway_0p2e5vq))
      (when (inclusive_counter_InclusiveGateway_0p2e5vq_1) (and (not (inclusive_counter_InclusiveGateway_0p2e5vq_1)) (inclusive_counter_InclusiveGateway_0p2e5vq_2)))
      (when (inclusive_counter_InclusiveGateway_0p2e5vq_0) (and (not (inclusive_counter_InclusiveGateway_0p2e5vq_0)) (inclusive_counter_InclusiveGateway_0p2e5vq_1)))
    )
  )

  (:action inclusive_decrease_InclusiveGateway_0p2e5vq
    :precondition (and (decrease_InclusiveGateway_0p2e5vq))
    :effect (and
      (not (decrease_InclusiveGateway_0p2e5vq))
      (when (inclusive_counter_InclusiveGateway_0p2e5vq_1) (and (not (inclusive_counter_InclusiveGateway_0p2e5vq_1)) (inclusive_counter_InclusiveGateway_0p2e5vq_0)))
      (when (inclusive_counter_InclusiveGateway_0p2e5vq_2) (and (not (inclusive_counter_InclusiveGateway_0p2e5vq_2)) (inclusive_counter_InclusiveGateway_0p2e5vq_1)))
    )
  )

  (:action inclusive_diverge_InclusiveGateway_0p2e5vq
    :precondition (and (InclusiveGateway_0p2e5vq))
    :effect (and
      (oneof
        (and (Task_12j0pib) (increase_InclusiveGateway_0p2e5vq) (at_least_one_branch_InclusiveGateway_0p2e5vq) (not (InclusiveGateway_0p2e5vq)))
        (and)
      )
      (oneof
        (and (Task_0jsoxba) (increase_InclusiveGateway_0p2e5vq) (at_least_one_branch_InclusiveGateway_0p2e5vq) (not (InclusiveGateway_0p2e5vq)))
        (and)
      )
    )
  )

  (:action inclusive_converge_InclusiveGateway_1dgb4sg
    :precondition (and (InclusiveGateway_1dgb4sg) (at_least_one_branch_InclusiveGateway_0p2e5vq) (inclusive_counter_InclusiveGateway_0p2e5vq_0))
    :effect (and (ExclusiveGateway_1ouv9kf) (not (InclusiveGateway_1dgb4sg)) (not (at_least_one_branch_InclusiveGateway_0p2e5vq)))
  )

  (:action Insure_parcel
    :precondition (and (Task_12j0pib) (not (branch_started_InclusiveGateway_0p2e5vq_Task_12j0pib)) (not (inclusive_counter_InclusiveGateway_0p2e5vq_0)))
    :effect (and (InclusiveGateway_1dgb4sg) (not (Task_12j0pib)) (branch_started_InclusiveGateway_0p2e5vq_Task_12j0pib) (decrease_InclusiveGateway_0p2e5vq))
  )

  (:action Write_package_label
    :precondition (and (Task_0jsoxba) (not (branch_started_InclusiveGateway_0p2e5vq_Task_0jsoxba)) (not (inclusive_counter_InclusiveGateway_0p2e5vq_0)))
    :effect (and (InclusiveGateway_1dgb4sg) (not (Task_0jsoxba)) (branch_started_InclusiveGateway_0p2e5vq_Task_0jsoxba) (decrease_InclusiveGateway_0p2e5vq))
  )

  (:action Clarify_shipment_method
    :precondition (and (Task_0vaxgaa))
    :effect (and (ExclusiveGateway_1mpgzhg) (not (Task_0vaxgaa)))
  )

  (:action Get_3_offers_from_logistic_companies
    :precondition (and (Task_0e6hvnj))
    :effect (and (Task_0s79ile) (not (Task_0e6hvnj)))
  )

  (:action Select_logistic_company_and_place_order
    :precondition (and (Task_0s79ile))
    :effect (and (ExclusiveGateway_1ouv9kf) (not (Task_0s79ile)))
  )

  (:action Package_goods
    :precondition (and (Task_05ftug5))
    :effect (and (ExclusiveGateway_0z5sib0) (test1) (not (Task_05ftug5)))
  )

  (:action Prepare_for_picking_up_goods
    :precondition (and (Task_0sl26uo))
    :effect (and (EndEvent_1fx9yp3) (not (Task_0sl26uo)))
  )

  (:action exclusive_Special_sandling_
    :precondition (and (ExclusiveGateway_1mpgzhg))
    :effect (and (oneof (InclusiveGateway_0p2e5vq) (Task_0e6hvnj)) (not (ExclusiveGateway_1mpgzhg)))
  )

  (:action exclusive_ExclusiveGateway_1ouv9kf
    :precondition (and (ExclusiveGateway_1ouv9kf))
    :effect (and (ExclusiveGateway_0z5sib0) (test2) (not (ExclusiveGateway_1ouv9kf)))
  )

  (:action parallel_ParallelGateway_02fgrfq
    :precondition (and (ParallelGateway_02fgrfq))
    :effect (and (Task_0vaxgaa) (Task_05ftug5) (not (ParallelGateway_02fgrfq)))
  )

  (:action parallel_ExclusiveGateway_0z5sib0
    :precondition (and (ExclusiveGateway_0z5sib0) (test1) (test2))
    :effect (and (Task_0sl26uo) (not (ExclusiveGateway_0z5sib0)))
  )

  (:action goal_Shipment_prepared
    :precondition (and (EndEvent_1fx9yp3))
    :effect (done)
  )

)